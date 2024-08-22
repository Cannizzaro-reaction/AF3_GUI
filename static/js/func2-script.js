//set slider number
const slider = document.getElementById('rangeSlider');
const output = document.getElementById('rangeValue');
output.textContent = slider.value;

slider.oninput = function () {
    output.textContent = this.value;
}

document.getElementById('confirmButton').addEventListener('click', function () {
    //set new title for the form
    var method = document.querySelector('input[name="method"]:checked').value;
    var chain = document.querySelector('input[name="chain"]:checked').value;
    var n = document.getElementById('rangeSlider').value;
    var titleText = `Top ${n} by ${method} (${chain})`;
    document.getElementById('resultTitle').textContent = `${titleText}`;

    //get dataframe
    const formData = new FormData();
    formData.append('rangeSlider', document.getElementById('rangeSlider').value);
    formData.append('chain', document.querySelector('input[name="chain"]:checked').value);
    formData.append('method', document.querySelector('input[name="method"]:checked').value);

    fetch('/count-interactions', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            console.log("Received data:", data);
            const tableContainer = document.getElementById('resultTable');
            tableContainer.innerHTML = generateTableHTML(data.data);
            bindRowClickEvents();

            // show download buttons
            const downloadButton = document.getElementById('downloadButton');
            downloadButton.style.display = 'block';
            downloadButton.onclick = function () {
                window.location.href = `/download-csv/${data.csvPath}`;
            };

            const fullDownloadButton = document.getElementById('fullDownloadButton');
            fullDownloadButton.style.display = 'block';
            fullDownloadButton.onclick = function () {
                window.location.href = `/download-csv/${data.fullPath}`;
            };
        })
        .catch(error => {
            console.error('Fetch error:', error);
        });
});

function generateTableHTML(data) {
    let tableHTML = '<table border="1"><tr>';
    // add columns in a fixed order
    const columnOrder = ["#", "Residue_ID", "Residue_Name", "Interaction_Count", "Total_Contact_Prob", "Average_B_Factor", "Average_PAE"];

    // Generate header
    columnOrder.forEach(header => {
        tableHTML += `<th>${header}</th>`;
    });
    tableHTML += '</tr>';

    // Generate rows
    data.forEach((row, index) => {
        tableHTML += '<tr>';
        tableHTML += `<th>${index + 1}</th>`;
        columnOrder.slice(1).forEach(key => {
            tableHTML += `<td>${row[key]}</td>`;
        });
        tableHTML += '</tr>';
    });

    tableHTML += '</table>';
    return tableHTML;
}

function bindRowClickEvents() {
    document.querySelectorAll('table tbody tr').forEach(row => {
        row.addEventListener('click', function () {
            // alert('Row clicked!');
            document.querySelectorAll('table tbody tr').forEach(row => {
                row.classList.remove('selected');
            });
            this.classList.add('selected');
        });
    });
}

function updateContent() {
    console.log("Radio option changed.");
}