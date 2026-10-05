import React, { useState } from 'react';
import { resumeAPI } from '../services/api';

const ResumeList = ({ resumes, onDeleted, onMatch, jobs }) => {
  const [selectedJobs, setSelectedJobs] = useState({});
  const [deletingId, setDeletingId] = useState(null);

  const handleDelete = async (resumeId) => {
    if (!window.confirm('Are you sure you want to delete this resume?')) {
      return;
    }

    try {
      setDeletingId(resumeId);
      await resumeAPI.delete(resumeId);
      onDeleted();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to delete resume.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleMatchClick = (resumeId) => {
    const jobId = selectedJobs[resumeId] || jobs[0]?.id;

    if (!jobId) {
      alert('Please create a job first.');
      return;
    }

    onMatch(jobId);
  };

  if (!resumes || resumes.length === 0) {
    return (
      <div className="empty-state">
        <h3>No resumes uploaded yet</h3>
        <p>Upload a resume to start screening candidates.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="section-heading">
        <h2>Uploaded Resumes</h2>
        <span className="count-badge">{resumes.length} Resumes</span>
      </div>

      <div className="resume-grid">
        {resumes.map((resume) => (
          <div className="resume-card" key={resume.id}>
            <div className="resume-card-header">
              <div className="file-icon">PDF</div>
              <div>
                <h3>{resume.filename}</h3>
                <p>Resume ID: {resume.id}</p>
              </div>
            </div>

            <div className="resume-stats">
              <div>
                <strong>{resume.skills?.length || 0}</strong>
                <span>Skills</span>
              </div>
              <div>
                <strong>{resume.experience?.length || 0}</strong>
                <span>Experience</span>
              </div>
              <div>
                <strong>{resume.education?.length || 0}</strong>
                <span>Education</span>
              </div>
            </div>

            <div className="resume-skills">
              <h4>Detected Skills</h4>
              <div className="skill-tags">
                {(resume.skills || []).slice(0, 5).map((skill, index) => (
                  <span className="skill-tag" key={index}>
                    {typeof skill === 'string' ? skill : skill.name}
                  </span>
                ))}
                {(resume.skills || []).length > 5 && (
                  <span className="skill-tag">
                    +{resume.skills.length - 5} more
                  </span>
                )}
              </div>
            </div>

            <div className="match-selector">
              <label htmlFor={`job-${resume.id}`}>Select Job</label>
              <select
                id={`job-${resume.id}`}
                value={selectedJobs[resume.id] || jobs[0]?.id || ''}
                onChange={(e) =>
                  setSelectedJobs({
                    ...selectedJobs,
                    [resume.id]: e.target.value
                  })
                }
              >
                {jobs.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.title}
                  </option>
                ))}
              </select>
            </div>

            <div className="resume-actions">
              <button
                className="btn-primary"
                onClick={() => handleMatchClick(resume.id)}
                disabled={jobs.length === 0}
              >
                Match Resume
              </button>

              <button
                className="btn-danger"
                onClick={() => handleDelete(resume.id)}
                disabled={deletingId === resume.id}
              >
                {deletingId === resume.id ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ResumeList;
