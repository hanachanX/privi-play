import streamlit as st
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from Crypto.Cipher import AES
from Crypto.Util import Counter
import hashlib
import json

st.set_page_config(page_title="PriviPlay", layout="wide")
st.title("🔒 Private Video Player")

def get_drive_service():
    token_info = json.loads(st.secrets["DRIVE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('drive', 'v3', credentials=creds)

PASSWORD = st.sidebar.text_input("Encryption Password", type="password")

if PASSWORD:
    service = get_drive_service()
    results = service.files().list(q="name contains '.enc'", fields="files(id, name)").execute()
    items = results.get('files', [])

    if items:
        selected = st.selectbox("動画を選択", items, format_func=lambda x: x['name'])
        
        if st.button("再生する"):
            # 鍵の生成
            KEY = hashlib.sha256(PASSWORD.encode()).digest()
            
            # 動画データの取得
            request = service.files().get_media(fileId=selected['id'])
            raw_data = request.execute()
            
            # 復号（最初の8バイトがnonce）
            nonce = raw_data[:8]
            encrypted_body = raw_data[8:]
            
            ctr = Counter.new(64, prefix=nonce)
            cipher = AES.new(KEY, AES.MODE_CTR, counter=ctr)
            decrypted_data = cipher.decrypt(encrypted_body)
            
            # 再生（Streamlitの標準ビデオプレイヤーに渡す）
            st.video(decrypted_data)
    else:
        st.info("動画が見つかりません。")
else:
    st.warning("左側のサイドバーに合言葉を入力してください。")