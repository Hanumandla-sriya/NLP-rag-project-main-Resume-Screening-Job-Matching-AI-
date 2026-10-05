import React, { useEffect, useState } from "react";
import { jobAPI } from "../services/api";

const getJobs = (data) => {
  console.log("RAW JOB DATA:", data);

  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.jobs)) {
    return data.jobs;
  }

  if (Array.isArray(data?.data)) {
    return data.data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  if (Array.isArray(data?.items)) {
    return data.items;
  }

  return [];
};

const getMatches = (data) => {
console.log("RAW MATCH DATA:", data);

console.log(
  "FIRST MATCH OBJECT:",
  JSON.stringify(
    Array.isArray(data)
      ? data[0]
      : data?.matches?.[0] ||
        data?.rankings?.[0] ||
        data?.results?.[0] ||
        data?.data?.[0],
    null,
    2
  )
);

  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.matches)) {
    return data.matches;
  }

  if (Array.isArray(data?.rankings)) {
    return data.rankings;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  if (Array.isArray(data?.data)) {
    return data.data;
  }

  return [];
};

const getJobId = (job) => {
  return job?.id ?? job?.job_id;
};

const getJobTitle = (job) => {
  return (
    job?.title ||
    job?.job_title ||
    job?.name ||
    "Untitled Job"
  );
};

const getSkills = (skills) => {
  if (!skills) {
    return [];
  }

  // Already an array
  if (Array.isArray(skills)) {
    return skills
      .flat(Infinity)
      .map((skill) => String(skill).trim())
      .filter(Boolean);
  }

  if (typeof skills === "string") {
    let text = skills
      .replace(/^\[|\]$/g, "")
      .replace(/["']/g, "")
      .trim()
      .toLowerCase();

    // Normal separators
    if (/[,;|\n]/.test(text)) {
      return text
        .split(/[,;|\n]+/)
        .map((skill) => skill.trim())
        .filter(Boolean);
    }

    /*
     * Backend is sometimes returning:
     *
     * data analysisedanumpypandaspythonsql
     *
     * Convert it back into individual skills.
     */

    const skillPatterns = [
      "data analysis",
      "machine learning",
      "deep learning",
      "generative ai",
      "natural language processing",
      "computer vision",
      "feature engineering",
      "prompt engineering",
      "scikit-learn",
      "scikit learn",
      "power bi",
      "data science",
      "tensorflow",
      "pytorch",
      "langchain",
      "matplotlib",
      "plotly",
      "python",
      "pandas",
      "numpy",
      "sql",
      "excel",
      "docker",
      "aws",
      "azure",
      "git",
      "rag",
      "nlp",
      "eda"
    ];

    const found = [];

    // Search from longest skill names to shortest
    skillPatterns
      .sort((a, b) => b.length - a.length)
      .forEach((skill) => {
        if (text.includes(skill)) {
          found.push(skill);
        }
      });

    // Remove duplicates
    return [...new Set(found)];
  }

  // Object containing skills
  if (typeof skills === "object") {
    return Object.values(skills)
      .flat(Infinity)
      .filter(Boolean)
      .map((skill) => String(skill).trim())
      .filter(Boolean);
  }

  return [];
};


const toPercentage = (score) => {
  const value = Number(score);

  if (!Number.isFinite(value)) {
    return 0;
  }

  if (value >= 0 && value <= 1) {
    return value * 100;
  }

  return Math.max(0, Math.min(100, value));
};

const ScoreBar = ({ label, score }) => {
  const percentage = toPercentage(score);

  return (
    <div className="score-item">
      <div className="score-label">
        <span>{label}</span>
        <strong>{percentage.toFixed(1)}%</strong>
      </div>

      <div className="score-bar">
        <div
          className="score-fill"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

const MatchResults = () => {
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [matches, setMatches] = useState([]);

  const [loadingJobs, setLoadingJobs] = useState(true);
  const [loadingMatches, setLoadingMatches] = useState(false);

  const [error, setError] = useState("");

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    try {
      setLoadingJobs(true);
      setError("");

      console.log("Loading jobs...");

      // jobAPI.getAll() ALREADY returns response.data
      const data = await jobAPI.getAll();

      console.log("Jobs API response:", data);

      const jobList = getJobs(data);

      console.log("Jobs found:", jobList);
      console.log("Number of jobs:", jobList.length);

      setJobs(jobList);

      if (jobList.length > 0) {
        const firstJobId = getJobId(jobList[0]);

        console.log("First job ID:", firstJobId);

        if (
          firstJobId !== undefined &&
          firstJobId !== null
        ) {
          setSelectedJobId(String(firstJobId));
        }
      }
    } catch (err) {
      console.error("Failed to load jobs:", err);

      setJobs([]);
      setSelectedJobId("");

      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Failed to load jobs."
      );
    } finally {
      setLoadingJobs(false);
    }
  };

  useEffect(() => {
    if (!selectedJobId) {
      setMatches([]);
      return;
    }

    loadRankings(selectedJobId);
  }, [selectedJobId]);

  const loadRankings = async (jobId) => {
    try {
      setLoadingMatches(true);
      setError("");

      console.log("Loading rankings for job:", jobId);

      // getRankings() ALSO already returns response.data
      const data = await jobAPI.getRankings(jobId);

      console.log("Rankings API response:", data);

      const matchList = getMatches(data);

      console.log("Matches found:", matchList);

      setMatches(matchList);
    } catch (err) {
      console.error("Failed to load rankings:", err);

      setMatches([]);

      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Failed to load rankings."
      );
    } finally {
      setLoadingMatches(false);
    }
  };

  const selectedJob = jobs.find(
    (job) =>
      String(getJobId(job)) ===
      String(selectedJobId)
  );

  return (
    <div className="match-results-container">

      <div className="page-header">
        <div>
          <h2>Match Results</h2>

          {selectedJob && (
            <p>
              Candidate rankings for{" "}
              <strong>
                {getJobTitle(selectedJob)}
              </strong>
            </p>
          )}
        </div>

        {matches.length > 0 && (
          <div className="candidate-count">
            <strong>{matches.length}</strong>{" "}
            candidates matched
          </div>
        )}
      </div>

      <div className="job-selector-card">

        <label htmlFor="job-select">
          Select Job to View Rankings
        </label>

        {loadingJobs ? (
          <div className="loading-state">
            Loading jobs...
          </div>
        ) : jobs.length === 0 ? (
          <div className="empty-state">
            <p>No jobs available.</p>
          </div>
        ) : (
          <select
            id="job-select"
            value={selectedJobId}
            onChange={(event) => {
              setSelectedJobId(event.target.value);
              setMatches([]);
              setError("");
            }}
          >
            <option value="">
              Select a job
            </option>

            {jobs.map((job, index) => {
              const jobId =
                getJobId(job) ?? index;

              return (
                <option
                  key={jobId}
                  value={jobId}
                >
                  {getJobTitle(job)}
                </option>
              );
            })}
          </select>
        )}
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {loadingMatches && (
        <div className="loading-state">
          Loading match results...
        </div>
      )}

      {!loadingMatches &&
        !error &&
        selectedJobId &&
        matches.length === 0 && (
          <div className="empty-state">
            <h3>No matching results</h3>

            <p>
              No candidates have been matched
              with this job yet.
            </p>
          </div>
        )}

      {!loadingMatches &&
        !selectedJobId &&
        jobs.length > 0 && (
          <div className="empty-state">
            <h3>Select a Job</h3>

            <p>
              Select a job above to view
              candidate rankings.
            </p>
          </div>
        )}

      {!loadingMatches &&
        matches.length > 0 && (
          <div className="match-results-grid">

            {matches.map((match, index) => {

              const overallScore =
                match?.overall_score ??
                match?.match_score ??
                match?.score ??
                0;

              const percentage =
                toPercentage(overallScore);

                const matchedSkills = getSkills(
                  match?.matched_skills ??
                  match?.matchedSkills ??
                  match?.skills_matched ??
                  match?.matched_skills_list ??
                  match?.matching_skills ??
                  match?.skills?.matched ??
                  []
                );
                
                const missingSkills = getSkills(
                  match?.missing_skills ??
                  match?.missingSkills ??
                  match?.skills_missing ??
                  match?.missing_skills_list ??
                  match?.missing_skills_required ??
                  match?.skills?.missing ??
                  []
                );

              const candidateName =
                match?.filename ||
                match?.resume_filename ||
                match?.candidate_name ||
                match?.name ||
                "Candidate";

              const rank =
                match?.rank ||
                index + 1;

              return (
                <div
                  className="match-card"
                  key={
                    match?.resume_id ||
                    match?.id ||
                    index
                  }
                >

                  <div className="match-card-header">

                    <div className="candidate-info">

                      <div className="rank-badge">
                        #{rank}
                      </div>

                      <div>
                        <h3>
                          {candidateName}
                        </h3>

                        <span className="match-label">
                          {percentage >= 80
                            ? "Excellent Match"
                            : percentage >= 60
                            ? "Moderate Match"
                            : "Low Match"}
                        </span>
                      </div>

                    </div>

                    <div className="overall-score">
                      <strong>
                        {percentage.toFixed(1)}%
                      </strong>

                      <span>
                        Overall Match
                      </span>
                    </div>

                  </div>

                  <div className="score-section">

                    <h4>
                      Score Breakdown
                    </h4>

                    <ScoreBar
                      label="Overall Match"
                      score={overallScore}
                    />

                    <ScoreBar
                      label="Skill Match"
                      score={
                        match?.skill_match_score ??
                        match?.skills_score ??
                        match?.skill_score ??
                        0
                      }
                    />

                    <ScoreBar
                      label="Experience"
                      score={
                        match?.experience_score ??
                        0
                      }
                    />

                    <ScoreBar
                      label="Education"
                      score={
                        match?.education_score ??
                        0
                      }
                    />

                    <ScoreBar
                      label="Semantic Similarity"
                      score={
                        match?.semantic_similarity ??
                        0
                      }
                    />

                  </div>

                  <div className="skill-explainability">

                    <div className="skill-section">

                      <div className="skill-section-header">

                        <h4>
                          🟢 Matched Skills
                        </h4>

                        <span className="skill-count">
                          {matchedSkills.length}
                        </span>

                      </div>

                      {matchedSkills.length > 0 ? (
                        <div className="skill-tags">

                          {matchedSkills.map(
                            (skill, skillIndex) => (
                              <span
                                className="skill-tag matched"
                                key={skillIndex}
                              >
                                {skill}
                              </span>
                            )
                          )}

                        </div>
                      ) : (
                        <p className="no-skills">
                          No matched skills.
                        </p>
                      )}

                    </div>

                    <div className="skill-section">

                      <div className="skill-section-header">

                        <h4>
                          🔴 Missing Skills
                        </h4>

                        <span className="skill-count">
                          {missingSkills.length}
                        </span>

                      </div>

                      {missingSkills.length > 0 ? (
                        <div className="skill-tags">

                          {missingSkills.map(
                            (skill, skillIndex) => (
                              <span
                                className="skill-tag missing"
                                key={skillIndex}
                              >
                                {skill}
                              </span>
                            )
                          )}

                        </div>
                      ) : (
                        <p className="no-skills">
                          No missing skills.
                        </p>
                      )}

                    </div>

                  </div>

                  <div className="candidate-rank">
                    Candidate Rank{" "}
                    <strong>
                      #{rank} of {matches.length}
                    </strong>
                  </div>

                </div>
              );
            })}

          </div>
        )}

    </div>
  );
};

export default MatchResults;