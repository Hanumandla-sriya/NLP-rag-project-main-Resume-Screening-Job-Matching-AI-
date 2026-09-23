import React, { useState, useEffect } from 'react';
import { jobAPI } from '../services/api';

const MatchResults = ({ results, onMatch, jobs, resumes }) => {
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [rankings, setRankings] = useState(null);

  useEffect(() => {
    if (results) {
      setSelectedJobId(results.job_id);
    }
  }, [results]);

  const handleLoadRankings = async (jobId) => {
    try {
      const data = await jobAPI.getRankings(jobId);
      setRankings(data);
    } catch (err) {
      console.error('Error loading rankings:', err);
    }
  };

  const displayResults = rankings || results;

  if (!displayResults || !displayResults.matches || displayResults.matches.length === 0) {
    return (
      <div className="card">
        <h2>Match Results</h2>
        {jobs.length > 0 && (
          <div>
            <label className="label">Select Job to View Rankings</label>
            <select
              className="input"
              value={selectedJobId || ''}
              onChange={(e) => {
                const jobId = parseInt(e.target.value);
                setSelectedJobId(jobId);
                handleLoadRankings(jobId);
              }}
            >
              <option value="">Select a job</option>
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title}
                </option>
              ))}
            </select>
          </div>
        )}
        <p style={{ marginTop: '20px' }}>
          {results ? 'No matches found.' : 'No results to display. Match candidates with a job to see results.'}
        </p>
      </div>
    );
  }

  const getScoreColor = (score) => {
    if (score >= 0.7) return '#28a745';
    if (score >= 0.5) return '#ffc107';
    return '#dc3545';
  };

  return (
    <div className="card">
      <h2>Match Results: {displayResults.job_title}</h2>
      <p>Total Matched: {displayResults.total_matched}</p>

      {jobs.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <label className="label">Select Job to View Rankings</label>
          <select
            className="input"
            value={selectedJobId || ''}
            onChange={(e) => {
              const jobId = parseInt(e.target.value);
              setSelectedJobId(jobId);
              handleLoadRankings(jobId);
            }}
          >
            <option value="">Select a job</option>
            {jobs.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title}
              </option>
            ))}
          </select>
        </div>
      )}

      <table className="table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Resume</th>
            <th>Overall Score</th>
            <th>Skill Match</th>
            <th>Experience</th>
            <th>Education</th>
            <th>Semantic Similarity</th>
          </tr>
        </thead>
        <tbody>
          {displayResults.matches.map((match) => (
            <tr key={match.resume_id}>
              <td>
                <span className="badge" style={{ backgroundColor: '#667eea', color: 'white' }}>
                  #{match.rank}
                </span>
              </td>
              <td>{match.filename}</td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <div
                    style={{
                      width: '100px',
                      height: '20px',
                      backgroundColor: '#e0e0e0',
                      borderRadius: '4px',
                      marginRight: '10px',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        width: `${match.overall_score * 100}%`,
                        height: '100%',
                        backgroundColor: getScoreColor(match.overall_score),
                      }}
                    />
                  </div>
                  <span>{(match.overall_score * 100).toFixed(1)}%</span>
                </div>
              </td>
              <td>{(match.skill_match_score * 100).toFixed(1)}%</td>
              <td>{(match.experience_score * 100).toFixed(1)}%</td>
              <td>{(match.education_score * 100).toFixed(1)}%</td>
              <td>{(match.semantic_similarity * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default MatchResults;
