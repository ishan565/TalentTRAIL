// Typed API client. Centralises the axios instance, JWT injection, and all
// backend calls so components never construct URLs or handle tokens directly.
import axios from "axios";

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const TOKEN_KEY = "talenttrail_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

const http = axios.create({ baseURL: BASE_URL });

http.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

http.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      clearToken();
      if (location.pathname !== "/login") location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export const api = {
  // auth
  async login(email, password) {
    const form = new URLSearchParams({ username: email, password });
    const { data } = await http.post("/auth/login", form);
    setToken(data.access_token);
    return data;
  },
  async register(email, password, full_name) {
    return (await http.post("/auth/register", { email, password, full_name })).data;
  },
  async me() {
    return (await http.get("/auth/me")).data;
  },

  // resume
  async uploadResume(file) {
    const fd = new FormData();
    fd.append("file", file);
    return (await http.post("/resume/upload", fd)).data;
  },
  async analyzeResume(id) {
    return (await http.post(`/resume/${id}/analyze`)).data;
  },
  async activeResume() {
    return (await http.get("/resume/active")).data;
  },

  // jobs
  async searchJobs(query, location, internships = false) {
    return (
      await http.get("/jobs/search", {
        params: { query, location, internships },
      })
    ).data.results;
  },
  async recommendations() {
    return (await http.get("/jobs/recommendations")).data.results;
  },
  async allJobs(limit = 50) {
    return (await http.get("/jobs/all", { params: { limit } })).data.results;
  },

  // full autonomous pipeline (all 9 agents end-to-end)
  async runPipeline(query, location) {
    return (
      await http.post("/pipeline/run", null, {
        params: { query, location: location || undefined },
        timeout: 180000,
      })
    ).data;
  },

  // analysis
  async atsScore(resume_id, job_id) {
    return (await http.post("/ats/score", { resume_id, job_id })).data;
  },
  async keywords(resume_id, job_id) {
    return (await http.post("/keywords/analyze", { resume_id, job_id })).data;
  },
  async optimize(resume_id, job_id) {
    return (await http.post("/resume/optimize", { resume_id, job_id })).data;
  },
  async coverLetter(resume_id, job_id, company_type) {
    return (
      await http.post("/cover-letter/generate", { resume_id, job_id, company_type })
    ).data;
  },

  // applications
  async applications() {
    return (await http.get("/applications")).data;
  },
  async createApplication(job_id, status = "saved") {
    return (await http.post("/applications", { job_id, status })).data;
  },
  async createManualApplication(payload) {
    return (await http.post("/applications/manual", payload)).data;
  },
  async updateApplication(id, status) {
    return (await http.patch(`/applications/${id}`, { status })).data;
  },

  // insights
  async analytics() {
    return (await http.get("/analytics")).data;
  },
  async roadmap() {
    return (await http.get("/career-roadmap")).data;
  },
};

export default http;
