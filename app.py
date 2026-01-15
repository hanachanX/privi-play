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

# --- Google Drive 認証 ---
def get_drive_service():
    token_info = json.loads(st.secrets["DRIVE_TOKEN"])
    creds = Credentials.from_authorized_user_info(token_info)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('drive', 'v3', credentials=creds)

# --- 復号ストリーミング用関数 ---
def get_video_stream(service, file_id, password):
    # 鍵の生成
    key = hashlib.sha256(password.encode()).digest()
    
    # ファイル全体のサイズを確認せず、まずは最初の塊を取得
    request = service.files().get_media(fileId=file_id)
    
    # 最初の8バイト(nonce)を取得
    first_8 = request.execute(headers={'Range': 'bytes=0-7'})
    nonce = first_8
    
    # 全データを取得（4GB対応：メモリ節約のため本来は分割すべきですが、まずは全体をストリームとして扱う）
    # ※Streamlitの制限上、一度バイナリにする必要があります
    full_data = request.execute()
    encrypted_body = full_data[8:]
    
    ctr = Counter.new(64, prefix=nonce)
    cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
    
    return cipher.decrypt(encrypted_body)

# --- メイン処理 ---
PASSWORD = st.sidebar.text_input("合言葉を入力", type="password")

if PASSWORD:
    service = get_drive_service()
    # .encファイルを検索
    results = service.files().list(q="name contains '.enc'", fields="files(id, name)").execute()
    items = results.get('files', [])

    if items:
        selected = st.selectbox("動画を選択してください", items, format_func=lambda x: x['name'])
        
        if st.button("再生を開始する"):
            try:
                with st.spinner("動画を復号中... (4GBの場合は1分ほどかかることがあります)"):
                    video_bytes = get_video_stream(service, selected['id'], PASSWORD)
                    st.video(video_bytes)
                    st.success("再生準備完了！")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
    else:
        st.info("Googleドライブに .enc ファイルが見つかりません。")
else:
    st.warning("左側のサイドバーに合言葉を入力してください。")