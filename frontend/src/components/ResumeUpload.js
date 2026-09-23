import React, { useState } from 'react';
import { resumeAPI } from '../services/api';

const ResumeUpload = ({ onUploaded }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const ext = selectedFile.name.split('.').pop().toLowerCase();
      if (ext !== 'pdf' && ext !== 'docx') {
        setMessage('Please select a PDF or DOCX file');
        return;
      }
      setFile(selectedFile);
      setMessage('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setMessage('Please select a file');
      return;
    }

    setUploading(true);
    setMessage('');

    try {
      await resumeAPI.upload(file);
      setMessage('Resume uploaded and processed successfully!');
      setFile(null);
      e.target.reset();
      if (onUploaded) {
        onUploaded();
      }
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Error uploading resume');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="card">
      <h2>Upload Resume</h2>
      {message && (
        <div className={`alert ${message.includes('success') ? 'alert-success' : 'alert-error'}`}>
          {message}
        </div>
      )}
      <form onSubmit={handleSubmit}>
        <div>
          <label className="label">Select Resume File (PDF or DOCX)</label>
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={handleFileChange}
            className="input"
            required
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={uploading}>
          {uploading ? 'Uploading...' : 'Upload Resume'}
        </button>
      </form>
    </div>
  );
};

export default ResumeUpload;
