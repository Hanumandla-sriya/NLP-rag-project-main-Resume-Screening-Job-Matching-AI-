import React, { useState } from 'react';
import { jobAPI } from '../services/api';

const JobForm = ({ onCreated }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    required_skills: '',
    preferred_skills: '',
    experience_level: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setMessage('');

    try {
      const jobData = {
        title: formData.title,
        description: formData.description,
        required_skills: formData.required_skills
          ? formData.required_skills.split(',').map((s) => s.trim())
          : [],
        preferred_skills: formData.preferred_skills
          ? formData.preferred_skills.split(',').map((s) => s.trim())
          : [],
        experience_level: formData.experience_level || null,
      };

      await jobAPI.create(jobData);
      setMessage('Job posting created successfully!');
      setFormData({
        title: '',
        description: '',
        required_skills: '',
        preferred_skills: '',
        experience_level: '',
      });
      if (onCreated) {
        onCreated();
      }
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Error creating job posting');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card">
      <h2>Create Job Posting</h2>
      {message && (
        <div className={`alert ${message.includes('success') ? 'alert-success' : 'alert-error'}`}>
          {message}
        </div>
      )}
      <form onSubmit={handleSubmit}>
        <div>
          <label className="label">Job Title *</label>
          <input
            type="text"
            name="title"
            className="input"
            value={formData.title}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <label className="label">Job Description *</label>
          <textarea
            name="description"
            className="textarea"
            value={formData.description}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <label className="label">Required Skills (comma-separated)</label>
          <input
            type="text"
            name="required_skills"
            className="input"
            value={formData.required_skills}
            onChange={handleChange}
            placeholder="e.g., Python, React, PostgreSQL"
          />
        </div>
        <div>
          <label className="label">Preferred Skills (comma-separated)</label>
          <input
            type="text"
            name="preferred_skills"
            className="input"
            value={formData.preferred_skills}
            onChange={handleChange}
            placeholder="e.g., Docker, AWS, Machine Learning"
          />
        </div>
        <div>
          <label className="label">Experience Level</label>
          <select
            name="experience_level"
            className="input"
            value={formData.experience_level}
            onChange={handleChange}
          >
            <option value="">Select level</option>
            <option value="entry">Entry Level</option>
            <option value="mid">Mid Level</option>
            <option value="senior">Senior Level</option>
          </select>
        </div>
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Creating...' : 'Create Job Posting'}
        </button>
      </form>
    </div>
  );
};

export default JobForm;
