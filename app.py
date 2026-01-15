import streamlit as st
from googleapiclient.discovery import build
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
                # --- 4GB対応: メモリ節約モード ---
                with st.spinner("接続を確立中..."):
                    # 1. 鍵の準備
                    key = hashlib.sha256(PASSWORD.encode()).digest()
                    
                    # 2. ファイルのダウンロード（ストリームとして取得）
                    request = service.files().get_media(fileId=selected['id'])
                    
                    # 最初の8バイト(nonce)だけをまず取得
                    nonce_data = request.execute(headers={'Range': 'bytes=0-7'})
                    
                    # 残りの全データを取得（※Streamlitのvideoタグへ渡すため一時的にバイナリ化）
                    # 本来はさらに分割したいところですが、まずはこの方式で試します
                    full_video_enc = request.execute()
                    
                    # 3. 復号処理
                    ctr = Counter.new(64, prefix=nonce_data)
                    cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
                    
                    # 最初の8バイトを除いた中身を復号
                    decrypted_video = cipher.decrypt(full_video_enc[8:])
                    
                    # 4. 再生
                    st.video(decrypted_video)
                    st.success("再生の準備ができました！")
            except Exception as e:
                st.error(f"エラーが発生しました。動画が大きすぎる可能性があります: {e}")
    else:
        st.info("動画が見つかりません。")