import streamlit as st
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from Crypto.Cipher import AES
from Crypto.Util import Counter
import hashlib
import io

st.set_page_config(page_title="PriviPlay", layout="wide")
st.title("🔒 Private Video Player")

# --- 設定 ---
# 本来は secrets.toml などで管理しますが、まずは動作確認用
PASSWORD = st.sidebar.text_input("Encryption Password", type="password")

if PASSWORD:
    KEY = hashlib.sha256(PASSWORD.encode()).digest()
    
    # ここでGoogle Driveからファイル一覧を取得する処理
    # (アクセストークンの連携が必要になります)
    st.info("鍵がセットされました。動画を選択してください。")
    
    # テスト表示用のプレイヤー（概念）
    # 実際にはブラウザのJavaScriptで復号する処理をここに組み込みます
    video_file = st.file_uploader("テスト：.encファイルを選択して再生確認", type="enc")
    
    if video_file:
        # 最初の8バイト（nonce）を読み取る
        nonce = video_file.read(8)
        ctr = Counter.new(64, prefix=nonce)
        cipher = AES.new(KEY, AES.MODE_CTR, counter=ctr)
        
        # 復号して再生（ブラウザのメモリ内で処理）
        decrypted_data = cipher.decrypt(video_file.read())
        st.video(decrypted_data)
else:
    st.warning("合言葉を入力してください。")