#!/usr/bin/env python3
"""
Convert VASCO DPX file to hexadecimal blob format
"""

def extract_token_data_from_dpx(dpx_content):
    """Extract key token data from DPX file"""
    lines = dpx_content.strip().split('\n')
    
    token_data = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('G0 '):
            # G0 SERNUMB8 IPIN PINLNG PINCHGLNG PINFORCED PINCHGON
            parts = line.split()
            if len(parts) >= 7:
                token_data['serial'] = parts[1]
                token_data['ipin'] = parts[2]
                token_data['pinlng'] = parts[3]
                token_data['pinchglng'] = parts[4]
                token_data['pinforced'] = parts[5]
                token_data['pinchgon'] = parts[6]
        
        elif line.startswith('A0 '):
            # A0 SERNUMB8 A_IVLEFT A_IVRIGHT A_OFFSET A_DES64KEY A_TDES64KEY
            parts = line.split()
            if len(parts) >= 7:
                token_data['serial'] = parts[1]
                token_data['iv_left'] = parts[2]
                token_data['iv_right'] = parts[3]
                token_data['offset'] = parts[4]
                token_data['des_key'] = parts[5]
                token_data['tdes_key'] = parts[6]
        
        elif line.startswith('GL '):
            # GL DPGO6 Y
            parts = line.split()
            if len(parts) >= 2:
                token_data['token_type'] = parts[1]
    
    return token_data

def create_vasco_blob(token_data):
    """Create a simplified VASCO blob from token data"""
    # This is a simplified approach - real VASCO blobs have specific binary format
    # For demonstration, we'll create a hex representation of the key data
    
    serial = token_data.get('serial', '')
    ipin = token_data.get('ipin', '')
    iv_left = token_data.get('iv_left', '')
    iv_right = token_data.get('iv_right', '')
    offset = token_data.get('offset', '')
    des_key = token_data.get('des_key', '')
    tdes_key = token_data.get('tdes_key', '')
    
    # Combine the hex data
    combined_data = serial + ipin + iv_left + iv_right + offset + des_key + tdes_key
    
    # Remove any non-hex characters and ensure it's proper hex
    hex_data = ''.join(c for c in combined_data if c in '0123456789ABCDEFabcdef')
    
    return hex_data.upper()

def main():
    """Main function to convert DPX to blob"""
    
    # Your DPX file content
    dpx_content = '''ZZ ----------------<        DPGO1 Export File             >----------------------------- 
DH FILE="GO1_10.DPX" DATE=27AUG2002 VERSION=1.5 CREATED_BY=BDEV 
DC HSH=0EE07880 DEL=0A97BE2F9380B33E 
DA A_HOST=APPL1 
ZZ 
ZZ ----------------<      Token Independent Fields        >----------------------------- 
DF GL TKTYPE CALCULATOR 
DF I0 A_APPLNAME A_CODEWORD A_RSPCHK A_RSPTY A_RSPLNG A_TDESFLAG 
ZZ 
ZZ ----------------<       Token Dependent Fields         >----------------------------- 
DF G0 SERNUMB8 IPIN PINLNG PINCHGLNG PINFORCED PINCHGON 
DF A0 SERNUMB8 A_IVLEFT A_IVRIGHT A_OFFSET A_DES64KEY A_TDES64KEY 
ZZ 
ZZ ------------------------------------------------------------------------------------- 
GL DPGO6 Y 
I0 "APPLI 1     " 00005200 N D 6 N 
G0 91234582 96BC2AAE 4 4 N Y 
A0 91234582 0CF1E7DE 7A76B04E 3B2AA0 97FE185D4658D6A3 D0A7FD20399E616F 
ZZ ------------------------------------------------------------------------------------- 
DE DEF_RECORDS=8 DATA_RECORDS=4 TOKENS=1 
ZZ ------------------------------------------------------------------------------------- '''
    
    print("VASCO DPX to Hex Blob Converter")
    print("=" * 50)
    
    # Extract token data
    token_data = extract_token_data_from_dpx(dpx_content)
    
    print("Extracted Token Data:")
    print("-" * 30)
    for key, value in token_data.items():
        print(f"{key}: {value}")
    
    # Create blob
    blob = create_vasco_blob(token_data)
    
    print(f"\nGenerated VASCO Token Blob:")
    print("-" * 30)
    print(blob)
    
    print(f"\nBlob Length: {len(blob)} characters")
    
    # Format for easier reading
    print(f"\nFormatted Blob (64 chars per line):")
    print("-" * 30)
    for i in range(0, len(blob), 64):
        print(blob[i:i+64])
    
    print(f"\nInstructions for PrivacyIDEA:")
    print("-" * 30)
    print("1. Copy the hex blob above")
    print("2. Paste it into the 'VASCO Token blob' field")
    print("3. Make sure 'use VASCO Serial' is checked")
    print("4. Complete the token enrollment")
    
    return blob

if __name__ == '__main__':
    blob = main()