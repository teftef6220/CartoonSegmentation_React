// import React, { useState } from 'react';
import React, { useState, ChangeEvent } from 'react';
import './App.css';

function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [processedImage, setProcessedImage] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);

  const [file, setFile] = useState(null);

  // 画像のアップロード
  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file){
      setUploadedImage(URL.createObjectURL(file));
      setFile(file); // ファイルオブジェクトを状態に保存
    } else {
      console.log("no file");
    }
  };
  
  // 画像処理の関数
  const handleProcessImage = async () => {
    try {
      const formData = new FormData();
      formData.append('file', file); // 保存したファイルオブジェクトを使用
    
      const response = await fetch('http://127.0.0.1:8000/run', {
        method: 'POST',
        body: formData,
      });
      //ここから先は、サーバーからのレスポンスを処理するコード
      if (response.ok) {
        const data = await response.json(); // サーバーがJSON形式で画像のURLを返すことを想定しています
        setProcessedImage(data.imageUrl || []); // 処理された画像のURLを状態にセット
        // console.log(data);
        // console.log(data.imageUrl);

      } else {
        throw new Error('Server responded with an error.');
      }
    } catch (error) {
      console.error('There was an error processing the image:', error);
    }

  };

  // 画像の保存
  const handleSaveImage = () => {
    if (!selectedImage) {
      alert('No image selected.');
      return;
    }
    const link = document.createElement('a');
    link.href = selectedImage;
    link.download = 'selected-image.png';
    document.body.appendChild(link);
    link.target = '_blank';
    link.click();
    document.body.removeChild(link);
  };

  // 画像の選択 一時的に選択された画像を状態に保存
  const selectImage = (imageUrl) => {
    setSelectedImage(imageUrl);
  };


  // processed フォルダの中身のサブフォルダを削除
  const handleDelete = async () => {
    const userConfirmed = window.confirm("本当に実行しますか？");
    if (userConfirmed) {
      try {
        const response = await fetch('http://127.0.0.1:8000/delete_image', {
          method: 'POST',
        });
      if (response.ok) {
          console.log("Folder contents deleted successfully");
        } else {
          console.log("Failed to delete folder contents");
        }
      } catch (error) {
        console.error('Error:', error);
      }
    } else {
      console.log("Cancelled");
    }
  };


  return (
    <div className="App">
      <h1 style={{ marginLeft: '20px', color: 'black' }}>Cartoon-Segmentation</h1>
      <div className="image-uploader">
        <input type="file" onChange={handleImageUpload} />
      </div>
      <div className="image-container">
        <div className="image-display">
          {uploadedImage && <img src={uploadedImage} alt="Uploaded" />}
        </div>
        <button onClick={handleProcessImage}>Process Image</button>
      </div>
      <div className="result-container">
        <div className="result-display">
          {processedImage.map((imageUrl, index) => (
            <img
              key={index}
              src={imageUrl}
              alt={`Processed ${index}`}
              onClick={() => selectImage(imageUrl)}
              className={selectedImage === imageUrl ? 'selected-image' : ''}
            />
          ))}
        </div>
        <button onClick={handleSaveImage} className="save-button">Save Image</button>
        <button onClick={handleDelete} className = "delete-button">Delete catch</button>
      </div>

      <footer>

        <p className = "page-footer">&copy; 2024 @hanyingcl</p>
      </footer>
    </div>
  );
}

export default App;
