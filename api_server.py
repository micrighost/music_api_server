import os
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Deemo 音樂電台 API 發射基地 🚀")

# 🎯 關鍵設定：允許跨網域連線 (CORS)
# 這可以確保你的手機 App 或是外部網頁在拍打這個 API 時不會被阻擋
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 允許所有人連線
    allow_credentials=True,
    allow_methods=["*"],      # 允許 GET, POST 等所有方法
    allow_headers=["*"],      # 允許所有自訂 Header
)

SONG_DIR = "songs"
IMAGE_DIR = "image"
COVER_IMAGE_NAME = "佩佩.jpg"

# ==========================================
# 🛰️ 基地發射台 1：取得電台基本資訊 (歌單與封面路徑)
# ==========================================
@app.get("/")
def read_root():
    return {
        "message": "歡迎來到 Deemo 音樂電台發射基地 🚀",
        "status": "running",
        "tip": "請前往 /api/info 查看完整歌單"
    }


@app.get("/api/info")
def get_radio_info():
    song_list = []
    if os.path.exists(SONG_DIR):
        # 自動掃描資料夾內所有的 mp3
        song_list = [f for f in os.listdir(SONG_DIR) if f.lower().endswith(".mp3")]
        song_list.sort()
        
    return {
        "status": "online",
        "total_songs": len(song_list),
        "song_list": song_list,
        "cover_image_url": "/api/cover"  # 告訴前端封面要去哪裡抓
    }

# ==========================================
# 🛰️ 基地發射台 2：獲取專輯封面圖片
# ==========================================
@app.get("/api/cover")
def get_cover_image():
    file_path = os.path.join(IMAGE_DIR, COVER_IMAGE_NAME)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="找不到封面圖片，請檢查 image 資料夾與檔名")

# ==========================================
# 🛰️ 基地發射台 3：HTTP 206 高階音訊串流服務
# ==========================================
@app.get("/api/music/{song_name}")
def stream_music(song_name: str, range: str = Header(None)):
    file_path = os.path.join(SONG_DIR, song_name)
    
    # 防呆機制：如果找不到該音樂檔案
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"找不到音樂檔案: {song_name}")
        
    file_size = os.path.getsize(file_path)
    
    # 🎯 處理行動裝置或播放器的 Range 請求 (HTTP 206 斷點續傳)
    if range:
        start, end = range.replace("bytes=", "").split("-")
        start = int(start)
        end = int(end) if end else file_size - 1
        chunk_size = (end - start) + 1
        
        # 每次只讀取播放器要求的那一小段音樂碎塊123333333
        def open_file_chunks():
            with open(file_path, "rb") as f:
                f.seek(start)
                yield f.read(chunk_size)
                
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type": "audio/mpeg",
        }
        return StreamingResponse(open_file_chunks(), status_code=206, headers=headers)
    
    # 如果播放器不支援 Range 請求，則直接吐出整首歌 (HTTP 200)
    def open_full_file():
        with open(file_path, "rb") as f:
            yield f.read()
            
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Type": "audio/mpeg",
    }
    return StreamingResponse(open_full_file(), status_code=200, headers=headers)
