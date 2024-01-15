from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import cv2

from PIL import Image
import numpy as np
import os

from animeinsseg import AnimeInsSeg, AnimeInstances
from animeinsseg.anime_instances import get_color

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ディレクトリ設定
UPLOAD_FOLDER = Path('uploads')
PROCESSED_FOLDER = Path('processed')
UPLOAD_FOLDER.mkdir(exist_ok=True)
PROCESSED_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.post("/run")
async def process_image(file: UploadFile = File(...)):
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type.")

    # ファイル保存
    file_path = UPLOAD_FOLDER / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 画像処理
    img = cv2.imread(str(file_path))
    #########
    # 画像処理のロジック
    ckpt = r'models/AnimeInstanceSegmentation/rtmdetl_e60.ckpt'

    mask_thres = 0.3
    instance_thres = 0.3
    refine_kwargs = {'refine_method': 'refinenet_isnet'} # set to None if not using refinenet

    net = AnimeInsSeg(ckpt, mask_thr=mask_thres, refine_kwargs=refine_kwargs)
    instances: AnimeInstances = net.infer(
        img,
        output_type='numpy',
        pred_score_thr=instance_thres
    )

    x = 0.5 ## 取りたい画像の大きさによって変える
    drawed = img.copy()
    im_h, im_w = img.shape[:2]
    img_with_alpha = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

    # instances.bboxes, instances.masks will be None, None if no obj is detected

    nb_object = len(list(zip(instances.bboxes, instances.masks)))

    for ii, (xywh, mask) in enumerate(zip(instances.bboxes, instances.masks)):
        color = get_color(ii)

        mask_alpha = 0.5
        linewidth = max(round(sum(img.shape) / 2 * 0.003), 2)

        # draw bbox
        p1, p2 = (int(xywh[0]), int(xywh[1])), (int(xywh[2] + xywh[0]), int(xywh[3] + xywh[1]))
        # cv2.rectangle(drawed, p1, p2, color, thickness=linewidth, lineType=cv2.LINE_AA)

        threshold_w = x * (int(im_w)/nb_object)
        threshold_h = x * (int(im_h)/nb_object)


        if int(xywh[2]) < threshold_w  and  int(xywh[3]) < threshold_h:
            print("too small")
            continue

        ## draw mask and cutout
        mask_uint8 = mask.astype(np.uint8) * 255
        # masked_img = cv2.bitwise_and(img, img, mask = mask)##アルファチャンネル使わないときはこれ
        img_with_alpha[:, :, 3] = mask_uint8
        # cv2.imwrite(f'output_images/masked_seg_{ii}_{img_name}.png', img_with_alpha)
        
        # draw mask
        p = mask.astype(np.float32)
        blend_mask = np.full((im_h, im_w, 3), color, dtype=np.float32)
        alpha_msk = (mask_alpha * p)[..., None]
        alpha_ori = 1 - alpha_msk
        drawed = drawed * alpha_ori + alpha_msk * blend_mask
    #########

    # 処理された画像を保存
    processed_path = PROCESSED_FOLDER / file.filename
    cv2.imwrite(str(processed_path), img_with_alpha) # ここで img_with_alpha を img に置き換え

    # クライアントに返すURLを生成（サーバーのURLを適切に設定してください）
    image_url = f"http://127.0.0.1:8000/processed/{file.filename}"
    return {"message": "File successfully processed", "imageUrl": image_url}

@app.get("/processed/{filename}")
async def uploaded_file(filename: str):
    file_path = PROCESSED_FOLDER / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(str(file_path))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
