// graph.js

// This function is called immediately when the page loads.
function setInitialTheme(isNightMode) {
    let textColor, backgroundColor;

    if (isNightMode) {
        textColor = '#f0f0f0';
        backgroundColor = '#333';
        document.body.classList.add('night-mode');
    } else {
        textColor = 'black';
        backgroundColor = 'white';
        document.body.classList.remove('night-mode');
    }

    document.body.style.backgroundColor = backgroundColor;
    document.body.style.color = textColor;
}

// This function is called when the 'Analyze' button is clicked.
function renderGraph(graphData, isNightMode) {
    if (typeof graphData === 'undefined' || graphData.length === 0) {
        d3.select("#graph").html("<p>No data to display for the selected tag.</p>");
        // Re-apply theme in case the page was just loaded
        setInitialTheme(isNightMode); 
        return;
    }
    
    d3.select("#graph").selectAll("*").remove();

    // Call setInitialTheme to ensure body styles are correct
    setInitialTheme(isNightMode);
    
    let textColor, borderColor;

    if (isNightMode) {
        textColor = '#f0f0f0';
        borderColor = '#555';
    } else {
        textColor = 'black';
        borderColor = '#d7d7d7';
    }

    const data = graphData;
  //  data.reverse();

    const container = document.getElementById('graph');
    const margin = { top: 40, right: 40, bottom: 50, left: 180 };
    const width = container.clientWidth - margin.left - margin.right;
    const height = container.clientHeight - margin.top - margin.bottom;

    if (width <= 0 || height <= 0) {
        return;
    }

    const svg = d3.select("#graph").append("svg")
        .attr("width", "100%")
        .attr("height", "100%")
        .attr("viewBox", `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
        .append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const tooltip = d3.select(".tooltip");

    const y = d3.scaleBand().range([0, height]).domain(data.map(d => d.label)).padding(0.1);
    const yAxis = svg.append("g").call(d3.axisLeft(y));
    yAxis.selectAll("text").style("fill", textColor).style("font-size", "12px");
    yAxis.selectAll(".domain, .tick line").style("stroke", borderColor);

    const x = d3.scaleLinear().domain([0, 100]).range([0, width]);
    const xAxis = svg.append("g").attr("transform", `translate(0, ${height})`).call(d3.axisBottom(x).ticks(10).tickFormat(d => d + '%'));
    xAxis.selectAll("text").style("fill", textColor).style("font-size", "12px");
    xAxis.selectAll(".domain, .tick line").style("stroke", borderColor);

    svg.append("text")
        .attr("text-anchor", "middle")
        .attr("x", width / 2).attr("y", height + margin.bottom - 10)
        .style("fill", textColor).style("font-weight", "bold").style("font-size", "14px")
        .text("Median Difficulty");

    svg.append("text")
        .attr("text-anchor", "middle")
        .attr("x", width / 2).attr("y", -15)
        .style("fill", textColor).style("font-weight", "bold").style("font-size", "16px")
        .text("Most Difficult Tag Groups");

    const colorScale = d3.scaleSequential(d3.interpolateRdYlGn).domain([100, 0]);

    svg.selectAll(".bar").data(data).enter().append("rect")
        .attr("class", "bar")
        .attr("y", d => y(d.label))
        .attr("x", x(0))
        .attr("width", d => x(d.value))
        .attr("height", y.bandwidth())
        .attr("fill", d => colorScale(d.value))
        .on("mouseover", function(event, d) {
            tooltip.style("opacity", 1);
        })
        .on("mousemove", function(event, d) {
            const percentageText = `<b>${d.value.toFixed(1)}%</b>`;
            tooltip.html(percentageText)
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 28) + "px");
        })
        .on("mouseout", function(event, d) {
            tooltip.style("opacity", 0);
        })
        .on("click", function(event, d) {
            pycmd('browseTag:' + d.fullTag);
        });
}