import React, { useState } from 'react';
import axios from 'axios';

function App() {
    const [image, setImage] = useState(null);
    const [result, setResult] = useState('');

    const handleImageChange = (e) => {
        setImage(e.target.files[0]);
    };

    const handleSubmit = async (e) => {
        if (e.key === 'Enter') {
            const formData = new FormData();
            formData.append('image', image);

            const response = await axios.post('http://localhost:3001/runscript', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            setResult(response.data);
        }
    };

    return (
        <div>
            <input type="file" onChange={handleImageChange} />
            <input type="text" onKeyDown={handleSubmit} />
            <div>{result}</div>
        </div>
    );
}

export default App;