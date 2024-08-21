document.getElementById('uploadForm').addEventListener('submit', function (event) {
    event.preventDefault(); // ban empty upload

    var formData = new FormData(this);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) { // check the success field
                // show different elements on the page after upload
                document.getElementById('uploadForm').classList.add('hidden');

                document.getElementById('clearUploads').classList.add('hidden');
                document.getElementById('clearFilesButton').classList.add('hidden');

                document.getElementById('message').classList.remove('hidden');
                document.getElementById('message').classList.add('visible');

                document.getElementById('returnLink').classList.remove('hidden');
                document.getElementById('returnLink').classList.add('visible');

                document.getElementById('buttonContainer').classList.remove('hidden');
                document.getElementById('buttonContainer').classList.add('visible');

                document.getElementById('chooseFunction').classList.remove('hidden');
                document.getElementById('chooseFunction').classList.add('visible');
            } else {
                alert('File upload failed.');
            }
        })
        .catch(error => console.error('Error:', error));

    // new page: Find residue pairs with highest interaction probability
    document.getElementById('findPairsButton').addEventListener('click', function () {
        window.location.href = "/find-residue-pairs";
    });

    // new page: Find residues with the most interactions or the highest total interaction probability
    document.getElementById('countInteraction').addEventListener('click', function () {
        window.location.href = "/count-interactions";
    });

    // new page: Visualize the interactions
    document.getElementById('visualize').addEventListener('click', function () {
        window.location.href = "/visualization";
    });

    // new page: Search interactions for a specific residue
    document.getElementById('search').addEventListener('click', function () {
        window.location.href = "/search";
    });
});

// show the page after upload
window.onload = function () {
    const urlParams = new URLSearchParams(window.location.search);
    const action = urlParams.get('action');

    if (action === 'showMessage') {
        // hide and show elements
        toggleElements();
        // rebind events to buttons
        bindButtonEvents();
    }
};

function toggleElements() {
    document.getElementById('uploadForm').classList.add('hidden');

    document.getElementById('clearUploads').classList.add('hidden');
    document.getElementById('clearFilesButton').classList.add('hidden');

    document.getElementById('message').classList.remove('hidden');
    document.getElementById('message').classList.add('visible');

    document.getElementById('returnLink').classList.remove('hidden');
    document.getElementById('returnLink').classList.add('visible');

    document.getElementById('buttonContainer').classList.remove('hidden');
    document.getElementById('buttonContainer').classList.add('visible');

    document.getElementById('chooseFunction').classList.remove('hidden');
    document.getElementById('chooseFunction').classList.add('visible');
};

function bindButtonEvents() {
    document.getElementById('findPairsButton').addEventListener('click', function () {
        window.location.href = "/find-residue-pairs";
    });

    document.getElementById('countInteraction').addEventListener('click', function () {
        window.location.href = "/count-interactions";
    });

    document.getElementById('visualize').addEventListener('click', function () {
        window.location.href = "/visualization";
    });

    document.getElementById('search').addEventListener('click', function () {
        window.location.href = "/search";
    });

    document.getElementById('returnLink').addEventListener('click', function () {
        window.location.href = "/";
    });
};

function clearUploads() {
    fetch('/clear-uploads', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Uploads cleared successfully!');
            } else {
                alert('Failed to clear uploads.');
            }
        })
        .catch(error => console.error('Error:', error));
}

document.getElementById('clearFilesButton').addEventListener('click', function () {
    fetch('/clear_files', {
        method: 'POST'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to clear files: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            alert(data.message);
        })
        .catch(error => {
            console.error('Fetch error:', error);
            alert('Error sending request: ' + error.message);
        });
});