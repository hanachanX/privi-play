import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from Crypto.Cipher import AES
from Crypto.Util import Counter
import hashlib
import json
import io

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
        selected = st.selectbox("動画を選択してください", items, format_func=lambda x: x['name'])
        
        if st.button("再生を開始"):
            try:
                with st.spinner("4GB動画をストリーミング中..."):
                    # 1. 鍵の準備
                    key = hashlib.sha256(PASSWORD.encode()).digest()
                    
                    # 2. 動画のダウンロード設定
                    request = service.files().get_media(fileId=selected['id'])
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    
                    # 最初の8バイト(nonce)を読み取る
                    done = False
                    while not done and fh.tell() < 8:
                        status, done = downloader.next_chunk()
                    
                    fh.seek(0)
                    nonce_data = fh.read(8)
                    
                    # 残りのデータをストリーミング（ここではメモリ節約のため一括復号を避ける）
                    # ※Streamlitのvideoタグへ渡すためにメモリ上に展開
                    while not done:
                        status, done = downloader.next_chunk()
                    
                    full_video_enc = fh.getvalue()
                    
                    # 3. 復号処理
                    ctr = Counter.new(64, prefix=nonce_data)
                    cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
                    
                    # 最初の8バイトを除いた中身を復号
                    decrypted_video = cipher.decrypt(full_video_enc[8:])
                    
                    # 4. 再生
                    st.video(decrypted_video)
                    st.success("再生準備完了！")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
    else:
        st.info("動画が見つかりません。")