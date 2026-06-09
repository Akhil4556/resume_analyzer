import { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);

  const uploadResume = async () => {
    try {
      if (!file) {
        alert("Please select a resume");
        return;
      }

      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(
        "https://re-a5f04dd6eec6467594872f0a528616a2.ecs.ap-south-1.on.aws/upload-resume/",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      console.log("Backend Response:", response.data);

      setResult(response.data);
    } catch (error) {
      console.error("FULL ERROR:", error);
      alert("Error uploading resume");
    }
  };

  return (
    <div className="container">
      <h1>AI Resume Analyzer</h1>

      <input
        type="file"
        accept=".pdf"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <br />
      <br />

      <button onClick={uploadResume}>
        Analyze Resume
      </button>

      {result && (
        <div className="card">
          <h2>Analysis Result</h2>

          <pre>{result.ai_feedback}</pre>
        </div>
      )}
    </div>
  );
}

export default App;