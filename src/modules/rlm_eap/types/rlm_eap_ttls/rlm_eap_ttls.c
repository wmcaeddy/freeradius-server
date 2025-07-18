/*
 *   This program is is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation; either version 2 of the License, or (at
 *   your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 *   You should have received a copy of the GNU General Public License
 *   along with this program; if not, write to the Free Software
 *   Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA
 */

/**
 * $Id$
 * @file rlm_eap_ttls.c
 * @brief EAP-TTLS as defined by RFC 5281
 *
 * @copyright 2003 Alan DeKok (aland@freeradius.org)
 * @copyright 2006 The FreeRADIUS server project
 */

RCSID("$Id$")
USES_APPLE_DEPRECATED_API	/* OpenSSL API has been deprecated by Apple */

#include <freeradius-devel/eap/tls.h>
#include "eap_ttls.h"

typedef struct {
	SSL_CTX		*ssl_ctx;		//!< Thread local SSL_CTX.
} rlm_eap_ttls_thread_t;

typedef struct {
	/*
	 *	TLS configuration
	 */
	char const	*tls_conf_name;
	fr_tls_conf_t	*tls_conf;

	/*
	 *	RFC 5281 (TTLS) says that the length field MUST NOT be
	 *	in fragments after the first one.  However, we've done
	 *	it that way for years, and no one has complained.
	 *
	 *	In the interests of allowing the server to follow the
	 *	RFC, we add the option here.  If set to "no", it sends
	 *	the length field in ONLY the first fragment.
	 */
	bool		include_length;

	/*
	 *	Virtual server for inner tunnel session.
	 */
	char const	*virtual_server;
	CONF_SECTION	*server_cs;

	/*
	 * 	Do we do require a client cert?
	 */
	bool		req_client_cert;
} rlm_eap_ttls_t;


static conf_parser_t submodule_config[] = {
	{ FR_CONF_OFFSET("tls", rlm_eap_ttls_t, tls_conf_name) },
	{ FR_CONF_DEPRECATED("copy_request_to_tunnel", rlm_eap_ttls_t, NULL), .dflt = "no" },
	{ FR_CONF_DEPRECATED("use_tunneled_reply", rlm_eap_ttls_t, NULL), .dflt = "no" },
	{ FR_CONF_OFFSET_FLAGS("virtual_server", CONF_FLAG_REQUIRED | CONF_FLAG_NOT_EMPTY, rlm_eap_ttls_t, virtual_server) },
	{ FR_CONF_OFFSET("include_length", rlm_eap_ttls_t, include_length), .dflt = "yes" },
	{ FR_CONF_OFFSET("require_client_cert", rlm_eap_ttls_t, req_client_cert), .dflt = "no" },
	CONF_PARSER_TERMINATOR
};

static fr_dict_t const *dict_freeradius;
static fr_dict_t const *dict_radius;

extern fr_dict_autoload_t rlm_eap_ttls_dict[];
fr_dict_autoload_t rlm_eap_ttls_dict[] = {
	{ .out = &dict_freeradius, .proto = "freeradius" },
	{ .out = &dict_radius, .proto = "radius" },
	{ NULL }
};

fr_dict_attr_t const *attr_eap_tls_require_client_cert;

fr_dict_attr_t const *attr_chap_challenge;
fr_dict_attr_t const *attr_ms_chap2_success;
fr_dict_attr_t const *attr_eap_message;
fr_dict_attr_t const *attr_ms_chap_challenge;
fr_dict_attr_t const *attr_reply_message;
fr_dict_attr_t const *attr_eap_channel_binding_message;
fr_dict_attr_t const *attr_user_name;
fr_dict_attr_t const *attr_user_password;
fr_dict_attr_t const *attr_vendor_specific;

extern fr_dict_attr_autoload_t rlm_eap_ttls_dict_attr[];
fr_dict_attr_autoload_t rlm_eap_ttls_dict_attr[] = {
	{ .out = &attr_eap_tls_require_client_cert, .name = "EAP-TLS-Require-Client-Cert", .type = FR_TYPE_UINT32, .dict = &dict_freeradius },

	{ .out = &attr_chap_challenge, .name = "CHAP-Challenge", .type = FR_TYPE_OCTETS, .dict = &dict_radius },
	{ .out = &attr_eap_message, .name = "EAP-Message", .type = FR_TYPE_OCTETS, .dict = &dict_radius },
	{ .out = &attr_ms_chap_challenge, .name = "Vendor-Specific.Microsoft.CHAP-Challenge", .type = FR_TYPE_OCTETS, .dict = &dict_radius },
	{ .out = &attr_ms_chap2_success, .name = "Vendor-Specific.Microsoft.CHAP2-Success", .type = FR_TYPE_OCTETS, .dict = &dict_radius },
	{ .out = &attr_reply_message, .name = "Reply-Message", .type = FR_TYPE_STRING, .dict = &dict_radius },
	{ .out = &attr_eap_channel_binding_message, .name = "Vendor-Specific.UKERNA.EAP-Channel-Binding-Message", .type = FR_TYPE_OCTETS, .dict = &dict_radius },
	{ .out = &attr_user_name, .name = "User-Name", .type = FR_TYPE_STRING, .dict = &dict_radius },
	{ .out = &attr_user_password, .name = "User-Password", .type = FR_TYPE_STRING, .dict = &dict_radius },
	{ .out = &attr_vendor_specific, .name = "Vendor-Specific", .type = FR_TYPE_VSA, .dict = &dict_radius },
	{ NULL }
};

/*
 *	Allocate the TTLS per-session data
 */
static ttls_tunnel_t *ttls_alloc(TALLOC_CTX *ctx, rlm_eap_ttls_t *inst)
{
	ttls_tunnel_t *t;

	t = talloc_zero(ctx, ttls_tunnel_t);
	t->server_cs = inst->server_cs;

	return t;
}

static unlang_action_t mod_handshake_resume(unlang_result_t *p_result, module_ctx_t const *mctx, request_t *request)
{
	eap_session_t		*eap_session = talloc_get_type_abort(mctx->rctx, eap_session_t);
	eap_tls_session_t	*eap_tls_session = talloc_get_type_abort(eap_session->opaque, eap_tls_session_t);
	fr_tls_session_t	*tls_session = eap_tls_session->tls_session;

	ttls_tunnel_t		*tunnel = talloc_get_type_abort(tls_session->opaque, ttls_tunnel_t);

	if ((eap_tls_session->state == EAP_TLS_INVALID) || (eap_tls_session->state == EAP_TLS_FAIL)) {
		REDEBUG("[eap-tls process] = %s", fr_table_str_by_value(eap_tls_status_table, eap_tls_session->state, "<INVALID>"));
	} else {
		RDEBUG2("[eap-tls process] = %s", fr_table_str_by_value(eap_tls_status_table, eap_tls_session->state, "<INVALID>"));
	}

	switch (eap_tls_session->state) {
	/*
	 *	EAP-TLS handshake was successful, tell the
	 *	client to keep talking.
	 *
	 *	If this was EAP-TLS, we would just return
	 *	an EAP-TLS-Success packet here.
	 */
	case EAP_TLS_ESTABLISHED:
		if (SSL_session_reused(tls_session->ssl)) {
			RDEBUG2("Skipping Phase2 due to session resumption");
			return eap_ttls_success(p_result, request, eap_session);
		}

		if (tunnel && tunnel->authenticated) return eap_ttls_success(p_result, request, eap_session);

		eap_tls_request(request, eap_session);
		RETURN_UNLANG_OK;

	/*
	 *	The TLS code is still working on the TLS
	 *	exchange, and it's a valid TLS request.
	 *	do nothing.
	 */
	case EAP_TLS_HANDLED:
		RETURN_UNLANG_HANDLED;

	/*
	 *	Handshake is done, proceed with decoding tunneled
	 *	data.
	 */
	case EAP_TLS_RECORD_RECV_COMPLETE:
		break;

	/*
	 *	Anything else: fail.
	 */
	default:
		RETURN_UNLANG_FAIL;
	}

	/*
	 *	Session is established, proceed with decoding
	 *	tunneled data.
	 */
	RDEBUG2("Session established.  Decoding Diameter attributes");

	/*
	 *	Process the TTLS portion of the request.
	 */
	return eap_ttls_process(p_result, request, eap_session, tls_session);
}

/*
 *	Do authentication, by letting EAP-TLS do most of the work.
 */
static unlang_action_t mod_handshake_process(UNUSED unlang_result_t *p_result, UNUSED module_ctx_t const *mctx,
					     request_t *request)
{
	eap_session_t		*eap_session = eap_session_get(request->parent);

	/*
	 *	Setup the resumption frame to process the result
	 */
	(void)unlang_module_yield(request, mod_handshake_resume, NULL, 0, eap_session);

	/*
	 *	Process TLS layer until done.
	 */
	return eap_tls_process(request, eap_session);
}

static unlang_action_t mod_session_init_resume(unlang_result_t *p_result, module_ctx_t const *mctx, request_t *request)
{
	rlm_eap_ttls_t		*inst = talloc_get_type_abort(mctx->mi->data, rlm_eap_ttls_t);
	rlm_eap_ttls_thread_t	*t = talloc_get_type_abort(mctx->thread, rlm_eap_ttls_thread_t);
	eap_session_t		*eap_session = eap_session_get(request->parent);

	eap_tls_session_t	*eap_tls_session;
	fr_tls_session_t	*tls_session;
	fr_pair_t		*vp;
	bool			client_cert;

	/*
	 *	EAP-TLS-Require-Client-Cert attribute will override
	 *	the require_client_cert configuration option.
	 */
	vp = fr_pair_find_by_da(&request->control_pairs, NULL, attr_eap_tls_require_client_cert);
	if (vp) {
		client_cert = vp->vp_uint32 ? true : false;
	} else {
		client_cert = inst->req_client_cert;
	}

	eap_session->opaque = eap_tls_session = eap_tls_session_init(request, eap_session, t->ssl_ctx, client_cert);
	if (!eap_tls_session) RETURN_UNLANG_FAIL;
	tls_session = eap_tls_session->tls_session;

	eap_tls_session->include_length = inst->include_length;

	/*
	 *	TLS session initialization is over.  Now handle TLS
	 *	related handshaking or application data.
	 */
	if (eap_tls_start(request, eap_session) < 0) {
		talloc_free(eap_tls_session);
		RETURN_UNLANG_FAIL;
	}

	tls_session->opaque = ttls_alloc(tls_session, inst);

	eap_session->process = mod_handshake_process;

	RETURN_UNLANG_OK;
}

/*
 *	Send an initial eap-tls request to the peer, using the libeap functions.
 */
static unlang_action_t mod_session_init(UNUSED unlang_result_t *p_result, module_ctx_t const *mctx, request_t *request)
{
	rlm_eap_ttls_t		*inst = talloc_get_type_abort(mctx->mi->data, rlm_eap_ttls_t);
	eap_session_t		*eap_session = eap_session_get(request->parent);

	eap_session->tls = true;

	(void) unlang_module_yield(request, mod_session_init_resume, NULL, 0, NULL);

	if (inst->tls_conf->new_session) return fr_tls_new_session_push(request, inst->tls_conf);

	return UNLANG_ACTION_CALCULATE_RESULT;
}

static int mod_thread_instantiate(module_thread_inst_ctx_t const *mctx)
{
	rlm_eap_ttls_t		*inst = talloc_get_type_abort(mctx->mi->data, rlm_eap_ttls_t);
	rlm_eap_ttls_thread_t	*t = talloc_get_type_abort(mctx->thread, rlm_eap_ttls_thread_t);

	t->ssl_ctx = fr_tls_ctx_alloc(inst->tls_conf, false);
	if (!t->ssl_ctx) return -1;

	return 0;
}

static int mod_thread_detach(module_thread_inst_ctx_t const *mctx)
{
	rlm_eap_ttls_thread_t	*t = talloc_get_type_abort(mctx->thread, rlm_eap_ttls_thread_t);

	if (likely(t->ssl_ctx != NULL)) SSL_CTX_free(t->ssl_ctx);
	t->ssl_ctx = NULL;

	return 0;
}

/*
 *	Attach the module.
 */
static int mod_instantiate(module_inst_ctx_t const *mctx)
{
	rlm_eap_ttls_t	*inst = talloc_get_type_abort(mctx->mi->data, rlm_eap_ttls_t);
	CONF_SECTION 	*conf = mctx->mi->conf;
	virtual_server_t const	*virtual_server = virtual_server_find(inst->virtual_server);

	if (!virtual_server) {
		cf_log_err_by_child(conf, "virtual_server", "Unknown virtual server '%s'", inst->virtual_server);
		return -1;
	}

	inst->server_cs = virtual_server_cs(virtual_server);
	if (!inst->server_cs) {
		cf_log_err_by_child(conf, "virtual_server", "Virtual server \"%s\" missing", inst->virtual_server);
		return -1;
	}

	/*
	 *	Read tls configuration, either from group given by 'tls'
	 *	option, or from the eap-tls configuration.
	 */
	inst->tls_conf = eap_tls_conf_parse(conf);
	if (!inst->tls_conf) {
		cf_log_err(conf, "Failed initializing SSL context");
		return -1;
	}

	return 0;
}

/*
 *	The module name should be the only globally exported symbol.
 *	That is, everything else should be 'static'.
 */
extern rlm_eap_submodule_t rlm_eap_ttls;
rlm_eap_submodule_t rlm_eap_ttls = {
	.common = {
		.magic			= MODULE_MAGIC_INIT,
		.name			= "eap_ttls",

		.inst_size		= sizeof(rlm_eap_ttls_t),
		.config			= submodule_config,
		.instantiate		= mod_instantiate,	/* Create new submodule instance */

		.thread_inst_size	= sizeof(rlm_eap_ttls_thread_t),
		.thread_instantiate	= mod_thread_instantiate,
		.thread_detach		= mod_thread_detach,
	},
	.provides		= { FR_EAP_METHOD_TTLS },
	.session_init		= mod_session_init,	/* Initialise a new EAP session */
};
