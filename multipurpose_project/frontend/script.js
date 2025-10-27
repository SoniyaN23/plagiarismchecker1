// tab switching code (keep if present)
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    // Hide all tab contents
    document.querySelectorAll(".tab-content").forEach(tab => tab.classList.add("hidden"));
    // Show the selected tab content
    document.getElementById(btn.dataset.tab).classList.remove("hidden");
  });
});

// --- Text Search: Uses /api/check ---
document.getElementById("check-text-btn").addEventListener("click", async () => {
  const textInput = document.getElementById('text-input').value;
  const fileInput = document.getElementById('text-file').files[0];
  const errorMessageDiv = document.getElementById('error-message');
  errorMessageDiv.textContent = ""; // Clear previous errors
  
  const form = new FormData();
  
  if (fileInput) {
    form.append('file', fileInput);
  } else if (textInput.trim() !== '') {
    form.append('text', textInput);
  } else {
    errorMessageDiv.textContent = "Please paste text or upload a file to check.";
    return;
  }
  
  try {
      // 1. Send data to Flask backend
      const resp = await fetch('/api/check', { 
          method: 'POST', 
          body: form 
      }); 
      
      const json = await resp.json();
      
      if (resp.ok) {
          // 2. Mock AI/Human data for frontend display (as calculated by app.py)
          json.ai = 45; // Based on app.py logic
          json.human = 55; // Based on app.py logic
          
          // Re-map the sources for the highlighted_sentences format expected by result.html
          // NOTE: json.sources is expected to be a list of objects: [{"url": "...", "excerpt": "..."}] 
          json.highlighted_sentences = json.sources.map(sourceObj => ({
              // Placeholder for specific sentence highlights, as backend only returns full text highlights.
              text: `Matching content detected (Excerpt: ${sourceObj.excerpt})`, 
              source: sourceObj.url,
              type: "exact" // Simplify to 'exact' for the placeholder
          }));
          
          json.suggestions = json.explanation; // Map backend's 'explanation' to frontend's 'suggestions'

          localStorage.setItem("plagiarismResult", JSON.stringify(json));
          window.location.href = "result.html";
      } else {
          // Handle API errors
          errorMessageDiv.textContent = `API Error: ${json.error || 'Check failed'}`;
      }
      
  } catch (error) {
      errorMessageDiv.textContent = `Network Error: ${error.message}`;
  }
});


// --- PDF Compare: Uses /api/compare_pdfs ---
document.getElementById("compare-pdf-btn").addEventListener("click", async () => {
  const pdf1 = document.getElementById("pdf1").files[0];
  const pdf2 = document.getElementById("pdf2").files[0];
  const errorMessageDiv = document.getElementById('error-message');
  errorMessageDiv.textContent = ""; // Clear previous errors
  
  if (!pdf1 || !pdf2) { 
      errorMessageDiv.textContent = "Please upload both PDFs for comparison.";
      return; 
  }

  const form = new FormData();
  form.append('file1', pdf1);
  form.append('file2', pdf2);

  try {
      // 1. Send data to Flask backend for comparison and PDF generation
      const resp = await fetch('/api/compare_pdfs', { 
          method: 'POST', 
          body: form 
      });
      
      const json = await resp.json();

      if (resp.ok) {
          // Mock data overlay for frontend display
          json.ai = 10;
          json.human = 90;
          json.suggestions = ["Review matching sentences in the downloaded PDF report.", "Consider rephrasing the top matching segments."];
          
          // Format top_matches for the highlighted_sentences display
          json.sources = json.top_matches ? json.top_matches.map((m, i) => ({ url: "Document 2 Match", excerpt: m.substring(0, 50) + "..." })) : [];
          json.highlighted_sentences = json.top_matches ? json.top_matches.map(m => ({ text: m, source: "Document 2 Match", type: "exact" })) : [];

          localStorage.setItem("plagiarismResult", JSON.stringify(json));
          window.location.href = "result.html";
      } else {
          errorMessageDiv.textContent = `PDF API Error: ${json.error || 'Comparison failed'}`;
      }
  } catch (error) {
       errorMessageDiv.textContent = `PDF Network Error: ${error.message}`;
  }
});

// --- Code Compare: Uses /api/check_code ---
document.getElementById("check-code-btn").addEventListener("click", async () => {
  // Get the files from the updated index.html inputs
  const code1 = document.getElementById("code1-file").files[0];
  const code2 = document.getElementById("code2-file").files[0];
  const errorMessageDiv = document.getElementById('error-message');
  errorMessageDiv.textContent = ""; // Clear previous errors
  
  if (!code1 || !code2) {
    errorMessageDiv.textContent = "Please upload both code files for comparison.";
    return;
  }

  const form = new FormData();
  form.append('file1', code1);
  form.append('file2', code2);

  try {
      // 1. Send data to Flask backend
      const resp = await fetch('/api/check_code', { 
          method: 'POST', 
          body: form 
      });
      
      const json = await resp.json();

      if (resp.ok) {
          // 2. Mock data overlay for frontend display (since code checker result is minimal)
          json.ai = 0; // Mock AI score
          json.human = 100; // Mock Human score
          
          // Use a simple text match for the highlights list
          json.highlighted_sentences = [
              { text: `Similarity Score: ${json.similarity}%`, source: "Code Comparison", type: "exact" },
              // Use the highlighted_code from the backend if available
              { text: `Highlighted Code Snippet: ${json.highlighted_code ? json.highlighted_code.substring(0, 50) + "..." : "See source files for highlights."}`, source: "Code Comparison", type: "paraphrase" }
          ];
          json.suggestions = ["Refactor duplicated code into a shared function.", "Use different variable names if the logic is unique."];
          json.sources = [{ url: "File 1: " + code1.name, excerpt: "Code comparison results." }, { url: "File 2: " + code2.name, excerpt: "Code comparison results." }];

          localStorage.setItem("plagiarismResult", JSON.stringify(json));
          window.location.href = "result.html";
      } else {
          errorMessageDiv.textContent = `Code API Error: ${json.error || 'Code check failed'}`;
      }
  } catch (error) {
       errorMessageDiv.textContent = `Code Network Error: ${error.message}`;
  }
});


// Placeholder for custom error messages (to replace alert())
document.addEventListener('DOMContentLoaded', () => {
    // Add a spot for error messages to the DOM if it doesn't exist
    const main = document.querySelector('main');
    if (main && !document.getElementById('error-message')) {
        const errorDiv = document.createElement('div');
        errorDiv.id = 'error-message';
        errorDiv.style.color = 'red';
        errorDiv.style.margin = '10px 0';
        errorDiv.style.fontWeight = 'bold';
        main.prepend(errorDiv);
    }
});