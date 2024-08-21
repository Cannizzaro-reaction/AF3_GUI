document.getElementById('confirmButton').addEventListener('click', function (event) {
    event.preventDefault(); // 阻止表单的默认提交行为

    // 设置表单标题
    var chain = document.querySelector('input[name="chain"]:checked').value;
    var resNum = document.getElementById('numberInput').value;
    var titleText = `Interactions Found for ${chain} ${resNum}`;
    document.getElementById('resultTitle').textContent = titleText;

    // 准备发送到服务器的数据
    const formData = new FormData();
    formData.append('chain', chain);
    formData.append('numberInput', resNum);

    // 发送请求到后端
    fetch('/search-residue', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to process request: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                console.log("Received data:", data.data);
                const tableContainer = document.getElementById('resultTable');
                tableContainer.innerHTML = generateTableHTML(data.data);
                bindRowClickEvents();

                // 显示下载按钮
                const downloadButton = document.getElementById('downloadButton');
                downloadButton.style.display = 'block'; // 显示按钮
                downloadButton.onclick = function () {
                    window.location.href = `/download-csv/${data.csvPath}`; // 设置按钮的点击行为
                };
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            alert('Error sending request: ' + error.message);
        });
});

function generateTableHTML(data) {
    if (!data || data.length === 0) {
        return '<p>No Interaction Found</p>';
    }

    let tableHTML = '<table border="1"><tr>';
    // add columns in a fixed order
    const columnOrder = ["#", "residue_number", "residue_name", "contact_probability", "b_factor", "PAE"];

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
            tableHTML += `<td>${row[key] ?? 'N/A'}</td>`;
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