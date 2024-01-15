import React, { useState } from 'react';
import './App.css';

function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [processedImage, setProcessedImage] = useState([]);

  const [file, setFile] = useState(null);

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    setUploadedImage(URL.createObjectURL(file));
    setFile(file); // ファイルオブジェクトを状態に保存
  };
  
  const handleProcessImage = async () => {
    try {
      const formData = new FormData();
      formData.append('file', file); // 保存したファイルオブジェクトを使用
    
      const response = await fetch('http://127.0.0.1:8000/run', {
        method: 'POST',
        body: formData,
      });
//ここから先は、サーバーからのレスポンスを処理するコードです。GPT にきこう！
      if (response.ok) {
        const data = await response.json(); // サーバーがJSON形式で画像のURLを返すことを想定しています
        setProcessedImage(data.imageUrl || []); // 処理された画像のURLを状態にセット
        console.log(data);
        console.log(data.imageUrl);

      } else {
        throw new Error('Server responded with an error.');
      }
    } catch (error) {
      console.error('There was an error processing the image:', error);
    }

  };


  const handleSaveImage = () => {
    // 処理された画像のURLを確認
    if (!processedImage) {
      alert('No processed image to save.');
      return;
    }
  
    // <a>要素を作成
    const link = document.createElement('a');
    link.href = processedImage; // 処理された画像のURL
    link.download = 'processed-image.png'; // 保存する際のデフォルトのファイル名
    link.target = '_blank'; // 新しいタブで開く
    // リンクをクリックしてダウンロードをトリガー
    document.body.appendChild(link);
    link.click();
  
    // リンクをドキュメントから削除
    document.body.removeChild(link);
  };

  return (
    <div className="App">
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
                    <img key={index} src={imageUrl} alt={`Processed ${index}`} />
                ))}
          </div>
          <button onClick={handleSaveImage} className="save-button">Save Image
    </button>
        </div>
      
    </div>
  );
}

export default App;
