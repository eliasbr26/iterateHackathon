/**
 * Fake LLM service for question difficulty evaluation
 * In production, this would call OpenAI or another LLM API
 */

/**
 * Evaluates the difficulty of a technical interview question
 * This is a placeholder function that simulates LLM difficulty scoring
 * 
 * @param text - The question text to evaluate
 * @returns A promise that resolves to a difficulty score (1-5)
 *          1 = Very Easy
 *          2 = Easy
 *          3 = Medium
 *          4 = Hard
 *          5 = Very Hard
 */
export async function evaluateQuestionDifficulty(text: string): Promise<number> {
  console.log(`[LLM] Evaluating difficulty for question: "${text.substring(0, 50)}..."`);
  
  // Simulate API delay (100-500ms)
  const delay = Math.floor(Math.random() * 400) + 100;
  await new Promise(resolve => setTimeout(resolve, delay));
  
  // Generate a random difficulty score between 1 and 5
  const difficulty = Math.floor(Math.random() * 5) + 1;
  
  console.log(`[LLM] Difficulty evaluation result: ${difficulty}/5`);
  
  return difficulty;
}

/**
 * Additional fake function to simulate question categorization
 * @param text - The question text
 * @returns A fake category
 */
export async function categorizeQuestion(_text: string): Promise<string> {
  const categories = [
    'Algorithms',
    'Data Structures',
    'System Design',
    'Coding',
    'Behavioral',
    'Problem Solving'
  ];
  
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 150));
  
  const category = categories[Math.floor(Math.random() * categories.length)];
  console.log(`[LLM] Question categorized as: ${category}`);
  
  return category;
}

/**
 * Fake function to analyze question complexity
 * @param text - The question text
 * @returns A complexity analysis object
 */
export async function analyzeQuestionComplexity(text: string): Promise<{
  wordCount: number;
  technicalTerms: number;
  estimatedTimeMinutes: number;
}> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 200));
  
  const wordCount = text.split(' ').length;
  const technicalTerms = Math.floor(Math.random() * 10) + 1;
  const estimatedTimeMinutes = Math.floor(Math.random() * 25) + 5;
  
  return {
    wordCount,
    technicalTerms,
    estimatedTimeMinutes
  };
}
