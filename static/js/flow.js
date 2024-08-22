    const data = {
        name: "BIAI",
        description: "A comprehensive application for analyzing resumes and providing job market insights",
        children: [
            {
                name: "User Interaction",
                description: "The initial point of contact for users",
                children: [
                    { name: "Authentication", description: "Users log in securely using Google OAuth" },
                    { name: "File Upload", description: "Users upload their resume in PDF or image format" },
                    { name: "Dashboard", description: "Users view analysis results and insights" }
                ]
            },
            {
                name: "Backend Processing",
                description: "Server-side operations for handling user requests and data processing",
                children: [
                    { 
                        name: "File Processing", 
                        description: "Extract text from uploaded resumes",
                        children: [
                            { name: "PDF Processing", description: "Extract text from PDF files using pdfplumber" },
                            { name: "Image Processing", description: "Extract text from images using Tesseract OCR" }
                        ]
                    },
                    { 
                        name: "Text Analysis", 
                        description: "Analyze extracted text to gather insights",
                        children: [
                            { name: "NLP", description: "Use Natural Language Processing techniques for text analysis" },
                            { name: "Keyword Extraction", description: "Identify key skills and experiences from the resume" }
                        ]
                    },
                    { 
                        name: "Job Market Comparison", 
                        description: "Compare resume content with current job market trends",
                        children: [
                            { name: "Serper API Integration", description: "Fetch real-time job market data" },
                            { name: "Similarity Analysis", description: "Compare resume keywords with job requirements" }
                        ]
                    },
                    { 
                        name: "AI-powered Suggestions", 
                        description: "Generate personalized improvement suggestions",
                        children: [
                            { name: "Ollama AI Integration", description: "Utilize AI for generating tailored advice" },
                            { name: "Suggestion Formatting", description: "Present AI-generated suggestions in a user-friendly format" }
                        ]
                    }
                ]
            },
            {
                name: "Data Management",
                description: "Handling and storing user data securely",
                children: [
                    { name: "Database Operations", description: "Store and retrieve user data using SQLAlchemy ORM" },
                    { name: "Session Management", description: "Manage user sessions for a seamless experience" },
                    { name: "Data Encryption", description: "Ensure user data is encrypted at rest and in transit" }
                ]
            },
            {
                name: "Output Generation",
                description: "Preparing and presenting analysis results to users",
                children: [
                    { name: "Resume Score", description: "Calculate an overall score based on various factors" },
                    { name: "Skill Gap Analysis", description: "Identify missing skills compared to job market demands" },
                    { name: "Potential Employers", description: "List companies that match the user's profile" },
                    { name: "Improvement Suggestions", description: "Provide actionable advice for enhancing the resume" }
                ]
            },
            {
                name: "System Management",
                description: "Ensuring smooth operation of the application",
                children: [
                    { name: "Error Handling", description: "Gracefully manage and log errors for debugging" },
                    { name: "Queue System", description: "Manage analysis requests to prevent system overload" },
                    { name: "Performance Monitoring", description: "Track system performance and optimize as needed" }
                ]
            }
        ]
    };
    
    document.addEventListener('DOMContentLoaded', function() {
        const mindmapElement = document.getElementById('mindmap');
        
        if (!mindmapElement) {
            console.error("Element with ID 'mindmap' not found.");
            return;
        }
        
        const width = mindmapElement.clientWidth;
        const height = 700;
        const margin = { top: 20, right: 120, bottom: 30, left: 120 };
    
        const svg = d3.select("#mindmap")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);
    
        const tree = d3.tree().size([height - margin.top - margin.bottom, width - margin.left - margin.right]);
    
        const root = d3.hierarchy(data);
        tree(root);
    
        const link = svg.selectAll(".link")
            .data(root.links())
            .enter().append("path")
            .attr("class", "link")
            .attr("d", d3.linkHorizontal()
                .x(d => d.y)
                .y(d => d.x));
    
        const node = svg.selectAll(".node")
            .data(root.descendants())
            .enter().append("g")
            .attr("class", "node")
            .attr("transform", d => `translate(${d.y},${d.x})`);
    
        node.append("circle")
            .attr("r", 6)
            .on("mouseover", showTooltip)
            .on("mouseout", hideTooltip);
    
        node.append("text")
            .attr("dy", ".31em")
            .attr("x", d => d.children ? -8 : 8)
            .style("text-anchor", d => d.children ? "end" : "start")
            .text(d => d.data.name);
    
        const tooltip = d3.select(".tooltip");
    
        function showTooltip(event, d) {
            const description = d.data.description || "No description available";
            tooltip.transition()
                .duration(200)
                .style("opacity", .9);
            tooltip.html(`<strong>${d.data.name}</strong><br>${description}`)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 28) + "px");
        }
    
        function hideTooltip() {
            tooltip.transition()
                .duration(500)
                .style("opacity", 0);
        }
    
        function updateMindMap() {
            const width = mindmapElement.clientWidth;
            d3.select("#mindmap svg").attr("width", width);
            tree.size([height - margin.top - margin.bottom, width - margin.left - margin.right]);
            tree(root);
    
            svg.selectAll(".link")
                .attr("d", d3.linkHorizontal()
                    .x(d => d.y)
                    .y(d => d.x));
    
            svg.selectAll(".node")
                .attr("transform", d => `translate(${d.y},${d.x})`);
        }
    
        // Add arrow markers for links
        svg.append("defs").selectAll("marker")
            .data(["end"])
            .enter().append("marker")
            .attr("id", "end")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 15)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#557a95");
    
        // Update links to use arrow markers
        link.attr("marker-end", "url(#end)");
    
        // Add subtle animation to nodes
        node.select("circle")
            .transition()
            .duration(800)
            .attrTween("r", function() {
                const i = d3.interpolate(0, 6);
                return function(t) { return i(t); };
            });
    
        // Add hover effect for links
        link.on("mouseover", function() {
            d3.select(this).transition()
                .duration(300)
                .attr("stroke-width", 4)
                .attr("stroke", "#4ecca3");
        })
        .on("mouseout", function() {
            d3.select(this).transition()
                .duration(300)
                .attr("stroke-width", 2)
                .attr("stroke", "#557a95");
        });
    
        // Animated flow particles
        function createFlowParticles() {
            link.each(function(d) {
                const linkElement = d3.select(this);
                const particleGroup = svg.append("g");
    
                function animateParticle() {
                    const particle = particleGroup.append("circle")
                        .attr("class", "flow-particle")
                        .attr("r", 2);
    
                    particle.transition()
                        .duration(2000)
                        .attrTween("transform", () => (t) => {
                            const p = linkElement.node().getPointAtLength(t * linkElement.node().getTotalLength());
                            return `translate(${p.x}, ${p.y})`;
                        })
                        .on("end", function() {
                            d3.select(this).remove();
                            animateParticle();
                        });
                }
    
                // Start multiple particles with delays
                for (let i = 0; i < 3; i++) {
                    setTimeout(animateParticle, i * 700);
                }
            });
        }
    
        createFlowParticles();
    });
    
    