from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import cv2
import glob

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

    # アップロードされた画像を保存
    file_path = UPLOAD_FOLDER / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 画像のファイル名を取得
    file_base_name = os.path.splitext(os.path.basename(file.filename))[0]
    image_urls = []

    # 画像処理
    img = cv2.imread(str(file_path))

    background_mask = np.ones(img.shape[:2], dtype=np.uint8) * 255
    #########

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

    im_h, im_w = img.shape[:2]
    img_with_alpha = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

    # instances.bboxes, instances.masks will be None, None if no obj is detected

    nb_object = len(list(zip(instances.bboxes, instances.masks)))

    for ii, (xywh, mask) in enumerate(zip(instances.bboxes, instances.masks)):
        
        
        # masked_img = cv2.bitwise_and(img, img, mask = mask)##アルファチャンネル使わないときはこれ
        # cv2.imwrite(f'output_images/masked_seg_{ii}_{img_name}.png', img_with_alpha)
        # draw mask
        # p = mask.astype(np.float32)
        # blend_mask = np.full((im_h, im_w, 3), color, dtype=np.float32)
        # alpha_msk = (mask_alpha * p)[..., None]
        # alpha_ori = 1 - alpha_msk
        # drawed = drawed * alpha_ori + alpha_msk * blend_mask

        # color = get_color(ii)
        # mask_alpha = 0.5
        # linewidth = max(round(sum(img.shape) / 2 * 0.003), 2)
        # draw bbox
        # p1, p2 = (int(xywh[0]), int(xywh[1])), (int(xywh[2] + xywh[0]), int(xywh[3] + xywh[1]))
        # cv2.rectangle(drawed, p1, p2, color, thickness=linewidth, lineType=cv2.LINE_AA)

        # calc threshold
        threshold_w = x * (int(im_w)/nb_object)
        threshold_h = x * (int(im_h)/nb_object)
        if int(xywh[2]) < threshold_w  and  int(xywh[3]) < threshold_h:
            print("too small")
            continue

        ## draw mask and cutout
        mask_uint8 = mask.astype(np.uint8) * 255
        img_with_alpha[:, :, 3] = mask_uint8

        # background_mask processing
        background_mask[mask.astype(bool)] = 0

        #make saving folder
        if ii == 0:
            processed_img_dir = PROCESSED_FOLDER / file_base_name
            processed_img_dir.mkdir(exist_ok=True)
                    
        # 処理された画像を保存
        processed_file_name = file_base_name + f"seg_{ii:04}_.png"
        processed_path = processed_img_dir / processed_file_name
        cv2.imwrite(str(processed_path), img_with_alpha) 

        image_url = f"http://127.0.0.1:8000/processed/{file_base_name}/{processed_file_name}"
        image_urls.append(image_url)

    #########
    # background_mask processing
    img_with_alpha[:, :, 3] = background_mask

    # save background image and url
    BG_file_name = file_base_name + f"seg_BG.png"
    background_image_url = f"http://127.0.0.1:8000/processed/{file_base_name}/{BG_file_name}"
    background_path = processed_img_dir / BG_file_name
    image_urls.append(background_image_url)
    cv2.imwrite(str(background_path), img_with_alpha)


    print(image_urls )
    return {"message": "File successfully processed", "imageUrl": image_urls}


@app.post("/delete_image")
async def delete_processed_file():
    full_path = PROCESSED_FOLDER 
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    # delete only sub folder not file
    # os.rmdir(full_path)
    all_file = glob.glob(str(full_path) + '/*')

    for folder in all_file:
        if os.path.isdir(folder):
            shutil.rmtree(folder) # フォルダごと削除
        else:
            pass
    return {"message": "File successfully deleted"}

# @app.get("/processed/{filename}")
# async def uploaded_file(filename: str):
#     file_path = PROCESSED_FOLDER / filename
#     if not file_path.is_file():
#         raise HTTPException(status_code=404, detail="File not found. ----------")
#     return FileResponse(str(file_path))

@app.get("/processed/{file_path:path}")
async def get_processed_file(file_path: str):
    full_path = PROCESSED_FOLDER / file_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(full_path))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
