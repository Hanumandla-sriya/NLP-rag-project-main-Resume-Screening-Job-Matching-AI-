import React from 'react';
import { jobAPI } from '../services/api';

const JobList = ({ jobs, onDeleted, onMatch, resumes }) => {
  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this job posting?')) {
      try {
        await jobAPI.delete(id);
        if (onDeleted) {
          onDeleted();
        }
      } catch (err) {
        alert('Error deleting job posting');
      }
    }
  };

  const handleMatchClick = async (jobId) => {
    if (resumes.length === 0) {
      alert('Please upload resumes first');
      return;
    }
    if (onMatch) {
      await onMatch(jobId);
    }
  };

  if (jobs.length === 0) {
    return (
      <div className="card">
        <p>No job postings created yet. Create a job posting to get started.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>Job Postings ({jobs.length})</h2>
      <table className="table">
        <thead>
          <tr>
            <th>Title</th>
            <th>Description</th>
            <th>Required Skills</th>
            <th>Experience Level</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id}>
              <td>{job.title}</td>
              <td>{job.description.substring(0, 100)}...</td>
              <td>
                {job.required_skills && job.required_skills.length > 0 ? (
                  <div>
                    {job.required_skills.slice(0, 3).map((skill, idx) => (
                      <span key={idx} className="badge badge-info" style={{ marginRight: '5px' }}>
                        {skill}
                      </span>
                    ))}
                    {job.required_skills.length > 3 && ` +${job.required_skills.length - 3} more`}
                  </div>
                ) : (
                  'N/A'
                )}
              </td>
              <td>{job.experience_level || 'N/A'}</td>
              <td>{new Date(job.created_at).toLocaleDateString()}</td>
              <td>
                <button
                  onClick={() => handleMatchClick(job.id)}
                  className="btn btn-primary"
                  style={{ marginRight: '5px', fontSize: '12px', padding: '5px 10px' }}
                >
                  Match Candidates
                </button>
                <button
                  onClick={() => handleDelete(job.id)}
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

export default JobList;
