export type HealthResponse = {
  status: string;
};

export type ExperienceItem = {
  title: string;
  company: string;
  period: string;
  description: string;
};

export type AnalysisResult = {
  summary: string;
  skills: string[];
  experience: ExperienceItem[];
  suggestions: string[];
};

export type ApiError = {
  detail: string;
};
