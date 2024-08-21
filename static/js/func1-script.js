const slider = document.getElementById('rangeSlider');
const output = document.getElementById('rangeValue');
output.textContent = slider.value;

slider.oninput = function () {
    output.textContent = this.value;
}

document.getElementById('confirmButton').addEventListener('click', function () {
    // alert('confirmed');

    const n = parseInt(document.getElementById('rangeValue').textContent);
    console.log("Selected n value:", n);

    fetch(`/generate_csv?n=${n}`, {
        method: 'POST'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            console.log("Received data:", data);
            const tableContainer = document.getElementById('resultTable');
            tableContainer.innerHTML = generateTableHTML(data.data);
            bindRowClickEvents();

            // 显示下载按钮
            const downloadButton = document.getElementById('downloadButton');
            downloadButton.style.display = 'block'; // 显示按钮
            downloadButton.onclick = function () {
                window.location.href = `/download-csv/${data.csvPath}`; // 设置按钮的点击行为
            };

            const fullDownloadButton = document.getElementById('fullDownloadButton');
            fullDownloadButton.style.display = 'block'; // 显示按钮
            fullDownloadButton.onclick = function () {
                window.location.href = `/download-csv/${data.fullPath}`; // 设置按钮的点击行为
            };
        })
        .catch(error => {
            console.error('Fetch error:', error);
        });
});

function generateTableHTML(data) {
    let tableHTML = '<table border="1"><tr>';
    const columnOrder = ["#", "Contact_Prob", "Chain_1", "Residue_1", "Residue_1_Name", "Chain_2", "Residue_2", "Residue_2_Name", "PAE", "Average_PAE_1", "Average_PAE_2", "Average_B_factor_1", "Average_B_factor_2"];

    // header
    columnOrder.forEach(header => {
        tableHTML += `<th>${header}</th>`;
    });
    tableHTML += '</tr>';

    // data
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