import React from 'react';
import { resumeAPI } from '../services/api';

const ResumeList = ({ resumes, onDeleted, onMatch, jobs }) => {
  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this resume?')) {
      try {
        await resumeAPI.delete(id);
        if (onDeleted) {
          onDeleted();
        }
      } catch (err) {
        alert('Error deleting resume');
      }
    }
  };

  const handleMatchClick = (resumeId) => {
    if (jobs.length === 0) {
      alert('Please create a job posting first');
      return;
    }
    const jobId = jobs[0].id; // Match with first job, or you can add a selector
    if (onMatch) {
      onMatch(jobId, [resumeId]);
    }
  };

  if (resumes.length === 0) {
    return (
      <div className="card">
        <p>No resumes uploaded yet. Upload a resume to get started.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>Uploaded Resumes ({resumes.length})</h2>
      <table className="table">
        <thead>
          <tr>
            <th>Filename</th>
            <th>Skills</th>
            <th>Experience</th>
            <th>Education</th>
            <th>Uploaded</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {resumes.map((resume) => (
            <tr key={resume.id}>
              <td>{resume.filename}</td>
              <td>
                {resume.skills && resume.skills.length > 0 ? (
                  <div>
                    {resume.skills.slice(0, 3).map((skill, idx) => (
                      <span key={idx} className="badge badge-info" style={{ marginRight: '5px' }}>
                        {skill}
                      </span>
                    ))}
                    {resume.skills.length > 3 && ` +${resume.skills.length - 3} more`}
                  </div>
                ) : (
                  'N/A'
                )}
              </td>
              <td>{resume.experience?.length || 0} entries</td>
              <td>{resume.education?.length || 0} entries</td>
              <td>{new Date(resume.created_at).toLocaleDateString()}</td>
              <td>
                <button
                  onClick={() => handleMatchClick(resume.id)}
                  className="btn btn-primary"
                  style={{ marginRight: '5px', fontSize: '12px', padding: '5px 10px' }}
                >
                  Match
                </button>
                <button
                  onClick={() => handleDelete(resume.id)}
                  className="btn btn-danger"
                  style={{ fontSize: '12px', padding: '5px 10px' }}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ResumeList;
