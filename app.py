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

# --- Google Drive 認証 (あなたのJSON専用の読み方) ---
def get_drive_service():
    try:
        # SecretsからDRIVE_TOKENを読み込む
        token_info = json.loads(st.secrets["DRIVE_TOKEN"])
        
        # サービスアカウント用ではなく、OAuthユーザー用の命令を使う(ここが重要)
        creds = Credentials.from_authorized_user_info(token_info)
        
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"認証エラーが発生しました: {e}")
        return None

# --- メイン画面 ---
PASSWORD = st.sidebar.text_input("Encryption Password", type="password")

if PASSWORD:
    service = get_drive_service()
    if service:
        try:
            # ドライブ内の .enc ファイルを検索
            results = service.files().list(
                q="name contains '.enc'", 
                fields="files(id, name)"
            ).execute()
            items = results.get('files', [])

            if not items:
                st.info("Googleドライブに .enc ファイルが見つかりませんでした。")
            else:
                selected_file = st.selectbox("動画を選択してください", items, format_func=lambda x: x['name'])
                
                if st.button("再生を開始"):
                    with st.spinner("4GB動画を復号中... 少し時間がかかります"):
                        # 鍵の生成
                        KEY = hashlib.sha256(PASSWORD.encode()).digest()
                        
                        # ファイルの取得
                        request = service.files().get_media(fileId=selected_file['id'])
                        file_data = request.execute()
                        
                        # 復号 (最初の8バイトがnonce)
                        nonce = file_data[:8]
                        encrypted_content = file_data[8:]
                        
                        ctr = Counter.new(64, prefix=nonce)
                        cipher = AES.new(KEY, AES.MODE_CTR, counter=ctr)
                        decrypted_video = cipher.decrypt(encrypted_content)
                        
                        # 動画表示
                        st.video(decrypted_video)
        
        except Exception as e:
            st.error(f"ドライブ通信エラー: {e}")
else:
    st.warning("左側のサイドバーに『合言葉』を入力してください。")