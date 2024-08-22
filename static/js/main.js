            // Function to scroll to the Resultz section
    function scrollToResults() {
        document.getElementById('Resultz').scrollIntoView({ behavior: 'smooth' });
    }

    // Simulate results being ready (you would call this when your results are available)
    function onResultsReady() {
        // Hide spinner, show results, etc.
        document.getElementById('spinner-div').style.display = 'none';
        document.getElementById('results').innerHTML = '<p>Results are here!</p>'; // Replace with actual results
        scrollToResults(); // Scroll to the results section
    }
        function printResults() {
    window.print();
}
function printResults() {
    const resultsContent = document.getElementById('results').innerHTML;
    const printWindow = window.open('', '', 'height=600,width=800');
    printWindow.document.write('<html><head><title>Print Analysis</title>');
    printWindow.document.write('<style>@media print { .no-print { display: none; } }</style>'); // Include print-specific styles
    printWindow.document.write('</head><body>');
    printWindow.document.write(resultsContent);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}

document.addEventListener('DOMContentLoaded', function () {
    // Toggle navigation menu
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');

    navToggle.addEventListener('click', function () {
        navMenu.classList.toggle('active');
    });

    // Register GSAP plugins
    gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

    // Form submission handler
    document.getElementById('resumeForm').addEventListener('submit', async function(event) {
        event.preventDefault();  // Prevent the default form submission

        // Check if user is logged in
        {% if not user %}
            alert('You need to log in to use this feature.');
            return;
        {% endif %}

        // Show the spinner
        document.getElementById('spinner-div').style.display = 'block';

        const formData = new FormData(this);  // Use 'this' to refer to the form

        try {
            const response = await fetch('/analyze_resume', {
                method: 'POST',
                body: formData
            });

            // Check for unauthorized status code
            if (response.status === 401) {
                document.getElementById('results').innerText = 'Error: You need to log in to access this feature.';
                return;
            }

            // Check if the response is JSON
            const contentType = response.headers.get('Content-Type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();

                if (data.error) {
                    document.getElementById('results').innerText = `Error: ${data.error}`;
                    return;
                }

                // Check if the user is in a queue
                if (data.queue_position !== undefined) {
                    document.getElementById('results').innerHTML = `
                        <strong>Queue Status:</strong> You are in position ${data.queue_position} of ${data.total_queue}. Please wait for your analysis to be processed.
                    `;
                    return;
                }

                // Display analysis results
                document.getElementById('results').innerHTML = `
                    <strong>Full Analysis:</strong> <pre>${data.full_analysis || 'No detailed analysis available'}</pre>
                    <strong>Potential Companies in India:</strong> <pre>${data.potential_companies_india || 'No data available'}</pre>
                    <strong>Potential Companies Globally:</strong> <pre>${data.potential_companies_global || 'No data available'}</pre>
                    <strong>India Job Market Similarity:</strong> <pre>${data.india_job_market_similarity || 'No data available'}</pre>
                    <strong>Global Job Market Similarity:</strong> <pre>${data.global_job_market_similarity || 'No data available'}</pre>
                    <strong>Example Similarity:</strong> <pre>${data.example_similarity || 'No data available'}</pre>
                `;

                // Scroll to results
                gsap.to(window, {duration: 1, scrollTo: "#results"});
            } else {
                throw new Error('Unexpected response type');
            }
        } catch (error) {
            document.getElementById('results').innerText = `Error: ${error.message}`;
        } finally {
            // Hide the spinner
            document.getElementById('spinner-div').style.display = 'none';

            // Show the results section
            document.getElementById('Resultz').style.display = 'block';
        }
    });
});
