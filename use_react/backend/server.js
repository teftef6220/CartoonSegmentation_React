const express = require('express');
const bodyParser = require('body-parser');
const { spawn } = require('child_process');
const path = require('path');
const app = express();
const port = 3001;

app.use(bodyParser.json());

app.post('/runscript', (req, res) => {
    // run.pyが存在するディレクトリの絶対パスを取得します。
    const pythonScriptPath = path.join(__dirname, '..', '..', 'run_react.py');
    const pythonScriptDir = path.dirname(pythonScriptPath);

    const pythonProcess = spawn('python', [pythonScriptPath, req.body.imagePath], { cwd: pythonScriptDir });

    pythonProcess.stdout.on('data', (data) => {
        res.send(data.toString());
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error('Error from Python script:', data.toString());
        res.status(500).send('An error occurred: ' + data.toString());
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python script exited with code ${code}`);
    });
});

app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});
