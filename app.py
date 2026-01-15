import streamlit as st
from googleapiclient.discovery import build
from google.oauth2 import service_account
from Crypto.Cipher import AES
from Crypto.Util import Counter
import hashlib
import json

st.set_page_config(page_title="PriviPlay", layout="wide")
st.title("🔒 Private Video Player")

# --- 設定 ---
# 合言葉（Secretsに設定したものをデフォルトに、画面でも入力可能にする）
default_pass = st.secrets.get("ENCRYPTION_PASSWORD", "")
PASSWORD = st.sidebar.text_input("Encryption Password", value=default_pass, type="password")

# Google Drive 認証
def get_drive_service():
    info = json.loads(st.secrets["DRIVE_TOKEN"])
    creds = service_account.Credentials.from_service_account_info(info)
    return build('drive', 'v3', credentials=creds)

if PASSWORD:
    KEY = hashlib.sha256(PASSWORD.encode()).digest()
    service = get_drive_service()

    # Google Driveから .enc ファイルを探す
    results = service.files().list(
        q="name contains '.enc'", fields="files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        st.write("Googleドライブに .enc ファイルが見つかりません。")
    else:
        # 動画を選択するセレクトボックス
        option = st.selectbox("再生する動画を選んでください", items, format_func=lambda x: x['name'])

        if st.button("再生開始"):
            # 動画をストリーミング（少しずつ読み込んで復号）
            file_id = option['id']
            # ※本来は巨大ファイル用に分割読み込みが必要ですが、まずは全体をストリーム再生
            request = service.files().get_media(fileId=file_id)
            
            # nonce (先頭8バイト) を取得
            content = request.execute()
            nonce = content[:8]
            encrypted_data = content[8:]
            
            # 復号
            ctr = Counter.new(64, prefix=nonce)
            cipher = AES.new(KEY, AES.MODE_CTR, counter=ctr)
            decrypted_data = cipher.decrypt(encrypted_data)
            
            # 再生
            st.video(decrypted_data)
else:

    st.warning("左側のサイドバーに合言葉を入力してください。")
