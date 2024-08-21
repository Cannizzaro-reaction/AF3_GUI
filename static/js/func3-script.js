document.getElementById('confirmButton').addEventListener('click', function (event) {
    event.preventDefault(); // Prevent the form from submitting via the browser
    const selectedChainInput = document.querySelector('input[name="chain"]:checked');

    if (!selectedChainInput) {
        alert("Please select a chain before confirming.");
        return;
    }

    const formData = new FormData();
    formData.append('chain', selectedChainInput.value);

    fetch('/generate_images', {
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
                document.getElementById('bubbleMap').src = "/images/bubble_map.png?time=" + new Date().getTime();
                document.getElementById('summary').src = "/images/interaction_summary.png?time=" + new Date().getTime();

                document.getElementById('bubbleMap').classList.remove('hidden');
                document.getElementById('summary').classList.remove('hidden');
                document.getElementById('downloadBubbleMap').classList.remove('hidden');
                document.getElementById('downloadSummary').classList.remove('hidden');

                // download the images
                document.getElementById('downloadBubbleMap').onclick = function () {
                    window.location.href = '/download-image/bubble_map.png';
                };
                document.getElementById('downloadSummary').onclick = function () {
                    window.location.href = '/download-image/interaction_summary.png';
                };
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error sending request: ' + error.message);
        });
});