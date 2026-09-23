import React, { useState, useEffect } from 'react';
import { resumeAPI, jobAPI } from '../services/api';
import ResumeUpload from './ResumeUpload';
import JobForm from './JobForm';
import ResumeList from './ResumeList';
import JobList from './JobList';
import MatchResults from './MatchResults';
import './Dashboard.css';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('resumes');
  const [resumes, setResumes] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [matchResults, setMatchResults] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadResumes();
    loadJobs();
  }, []);

  const loadResumes = async () => {
    try {
      const data = await resumeAPI.getAll();
      setResumes(data);
    } catch (err) {
      console.error('Error loading resumes:', err);
    }
  };

  const loadJobs = async () => {
    try {
      const data = await jobAPI.getAll();
      setJobs(data);
    } catch (err) {
      console.error('Error loading jobs:', err);
    }
  };

  const handleResumeUploaded = () => {
    loadResumes();
  };

  const handleJobCreated = () => {
    loadJobs();
  };

  const handleResumeDeleted = () => {
    loadResumes();
  };

  const handleJobDeleted = () => {
    loadJobs();
    setSelectedJob(null);
    setMatchResults(null);
  };

  const handleMatch = async (jobId, resumeIds = null) => {
    setLoading(true);
    try {
      const results = await jobAPI.match(jobId, resumeIds);
      setMatchResults(results);
      setActiveTab('results');
    } catch (err) {
      console.error('Error matching:', err);
      alert('Error matching candidates. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Resume Screening AI</h1>
        <button onClick={handleLogout} className="btn btn-secondary">
          Logout
        </button>
      </header>

      <div className="dashboard-tabs">
        <button
          className={`tab ${activeTab === 'resumes' ? 'active' : ''}`}
          onClick={() => setActiveTab('resumes')}
        >
          Resumes
        </button>
        <button
          className={`tab ${activeTab === 'jobs' ? 'active' : ''}`}
          onClick={() => setActiveTab('jobs')}
        >
          Jobs
        </button>
        <button
          className={`tab ${activeTab === 'results' ? 'active' : ''}`}
          onClick={() => setActiveTab('results')}
        >
          Match Results
        </button>
      </div>

      <div className="dashboard-content">
        {activeTab === 'resumes' && (
          <div>
            <ResumeUpload onUploaded={handleResumeUploaded} />
            <ResumeList
              resumes={resumes}
              onDeleted={handleResumeDeleted}
              onMatch={handleMatch}
              jobs={jobs}
            />
          </div>
        )}

        {activeTab === 'jobs' && (
          <div>
            <JobForm onCreated={handleJobCreated} />
            <JobList
              jobs={jobs}
              onDeleted={handleJobDeleted}
              onMatch={handleMatch}
              resumes={resumes}
            />
          </div>
        )}

        {activeTab === 'results' && (
          <MatchResults
            results={matchResults}
            onMatch={handleMatch}
            jobs={jobs}
            resumes={resumes}
          />
        )}
      </div>

      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner">Processing...</div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
