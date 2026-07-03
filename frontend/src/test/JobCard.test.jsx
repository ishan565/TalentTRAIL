import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import JobCard from "../components/JobCard";

const sample = {
  job: {
    id: 1,
    title: "Backend Engineer",
    company: "Acme AI",
    location: "Remote",
    skills: ["python", "fastapi"],
    source: "greenhouse",
  },
  final_score: 0.82,
  keyword_score: 0.5,
  semantic_score: 0.9,
  ats_score: 0.7,
  recency_score: 0.8,
  explanation: { why: "Strongest signal: semantic." },
};

describe("JobCard", () => {
  it("renders job title, company and match percentage", () => {
    render(<JobCard ranked={sample} />);
    expect(screen.getByText("Backend Engineer")).toBeInTheDocument();
    expect(screen.getByText("Acme AI")).toBeInTheDocument();
    expect(screen.getByText("82% match")).toBeInTheDocument();
  });
});
