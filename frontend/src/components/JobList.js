
import React, { useState } from 'react';
import { jobAPI } from '../services/api';

const JobList = ({ jobs, onDeleted, onMatch, resumes }) => {
  const [deletingId, setDeletingId] = useState(null);
  const [matchingId, setMatchingId] = useState(null);

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this job posting?')) {
      return;
    }

    try {
      setDeletingId(id);
      await jobAPI.delete(id);
      if (onDeleted) onDeleted();
    } catch (err) {
      alert('Error deleting job posting. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleMatchClick = async (jobId) => {
    if (!resumes || resumes.length === 0) {
      alert('Please upload resumes first.');
      return;
    }

    try {
      setMatchingId(jobId);
      if (onMatch) {
        await onMatch(jobId);
      }
    } finally {
      setMatchingId(null);
    }
  };

  if (!jobs || jobs.length === 0) {
    return (
      <div className="card empty-state">
        <div className="empty-icon">💼</div>
        <h3>No job postings yet</h3>
        <p>Create your first job posting to start matching candidates.</p>
      </div>
    );
  }

  return (
    <section className="card job-section">
      <div className="section-heading">
        <div>
          <h2>Job Postings</h2>
          <p>Manage open positions and discover suitable candidates.</p>
        </div>
        <span className="count-badge">{jobs.length} Jobs</span>
      </div>

      <div className="job-grid">
        {jobs.map((job) => (
          <article className="job-card" key={job.id}>
            <div className="job-card-header">
              <div className="job-icon">💼</div>
              <div className="job-title-info">
                <h3>{job.title}</h3>
                <span className="experience-badge">
                  {job.experience_level || 'Not specified'}
                </span>
              </div>
            </div>

            <div className="job-description">
              <p>
                {job.description?.length > 180
                  ? `${job.description.substring(0, 180)}...`
                  : job.description}
              </p>
            </div>

            <div className="job-skills">
              <h4>Required Skills</h4>

              {job.required_skills?.length > 0 ? (
                <div className="skill-tags">
                  {job.required_skills.map((skill, idx) => (
                    <span className="skill-tag" key={`${job.id}-${idx}`}>
                      {skill}
                    </span>
                  ))}
                </div>
              ) : (
                <span className="muted-text">No required skills specified</span>
              )}
            </div>

            {job.preferred_skills?.length > 0 && (
              <div className="job-skills preferred-skills">
                <h4>Preferred Skills</h4>
                <div className="skill-tags">
                  {job.preferred_skills.slice(0, 5).map((skill, idx) => (
                    <span className="preferred-skill-tag" key={`${job.id}-p-${idx}`}>
                      {skill}
                    </span>
                  ))}
                  {job.preferred_skills.length > 5 && (
                    <span className="more-skills">
                      +{job.preferred_skills.length - 5} more
                    </span>
                  )}
                </div>
              </div>
            )}

            <div className="job-footer">
              <span>
                Created {new Date(job.created_at).toLocaleDateString()}
              </span>
              <span>Job ID: #{job.id}</span>
            </div>

            <div className="job-actions">
              <button
                className="btn btn-primary"
                onClick={() => handleMatchClick(job.id)}
                disabled={matchingId === job.id || !resumes?.length}
              >
                {matchingId === job.id ? 'Matching...' : 'Match Candidates'}
              </button>

              <button
                className="btn btn-danger"
                onClick={() => handleDelete(job.id)}
                disabled={deletingId === job.id}
              >
                {deletingId === job.id ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
};

export default JobList;