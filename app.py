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

# --- Google Drive 認証 (通行証を使ってログイン) ---
def get_drive_service():
    try:
        # Secrets から JSON 文字列を読み込む
        token_info = json.loads(st.secrets["DRIVE_TOKEN"])
        
        # 通行証（Credentials）を作成
        creds = Credentials.from_authorized_user_info(token_info)
        
        # もし通行証の期限が切れていたら自動更新する
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"認証データの読み込みに失敗しました: {e}")
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
                
                if st.button("再生準備"):
                    # 4GBの再生は重いので、まずは「読み込み成功」を出す
                    st.success(f"「{selected_file['name']}」の準備をしています。合言葉を確認中...")
                    
                    # 鍵の生成
                    KEY = hashlib.sha256(PASSWORD.encode()).digest()
                    
                    # ここで動画データを取得（まずはテストとして全読み込み）
                    # ※4GBの場合、ここから先はメモリ対策の別コードが必要になります
                    st.warning("現在、4GB動画の再生に必要な『分割ダウンロード機能』を準備しています。リストが表示されたら教えてください！")
        
        except Exception as e:
            st.error(f"ドライブへのアクセス中にエラーが発生しました: {e}")
else:
    st.warning("左側のサイドバーに『合言葉』を入力してください。")