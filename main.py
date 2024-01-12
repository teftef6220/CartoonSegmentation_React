from flask_cors import CORS

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
from PIL import Image
import io

import cv2
from PIL import Image
import numpy as np
import os

from animeinsseg import AnimeInsSeg, AnimeInstances
from animeinsseg.anime_instances import get_color

app = Flask(__name__)
CORS(app)

# このディレクトリにアップロードされたファイルを保存します
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/run', methods=['POST'])
def process_image():
    if 'file' not in request.files:
        app.logger.error('No file part in the request')
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        app.logger.error('No file selected for uploading')
        return jsonify({'error': 'No file selected for uploading'}), 400
    

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # ここで画像処理を行います
        # 例: PILを使用して画像を開き、何らかの処理を行う
        img = cv2.imread(file_path)

        ##################################
        # 画像処理のロジックをここに実装...

        ckpt = r'models/AnimeInstanceSegmentation/rtmdetl_e60.ckpt'
        # ckpt = "I:/CartoonSegmentation/models/AnimeInstanceSegmentation/rtmdetl_e60.ckpt"

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
        processed_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
        cv2.imwrite(processed_path, img_with_alpha)
        # img_with_alpha.save(processed_path)

        print(request.host_url + 'processed/' + filename)

        # 処理した画像へのパスをクライアントに返します
        return jsonify({'message': 'File successfully processed','imageUrl': request.host_url + 'processed/' + filename}), 200
        # return jsonify({'imageUrl': request.host_url + 'processed/' + filename}), 200

# 処理された画像をクライアントに提供するルート
@app.route('/processed/<filename>')
def uploaded_file(filename):
    print("here")
    return send_file(os.path.join(app.config['PROCESSED_FOLDER'], filename))

if __name__ == '__main__':
    app.run(debug=True)

