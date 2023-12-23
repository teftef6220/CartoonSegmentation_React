import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [outputImage, setOutputImage] = useState(null);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    setSelectedImage(file);
    setPreview(URL.createObjectURL(file));
  };

  const handleRunScript = async () => {
    const formData = new FormData();
    formData.append('image', selectedImage);

    try {
      const response = await axios.post('http://localhost:3001/runscript', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        responseType: 'blob' // Important for receiving the image as a blob
      });

      // Create a URL for the blob
      const outputImageUrl = URL.createObjectURL(response.data);
      setOutputImage(outputImageUrl);
    } catch (error) {
      console.error('There was an error!', error);
    }
  };

  return (
    <div>
      <input type="file" onChange={handleImageChange} />
      {preview && (
        <div>
          <img src={preview} alt="Selected" style={{ height: '100px' }} />
          <button onClick={handleRunScript}>RUN</button>
        </div>
      )}
      {outputImage && (
        <div>
          <img src={outputImage} alt="Output" style={{ height: '100px' }} />
        </div>
      )}
    </div>
  );
}

export default App;

