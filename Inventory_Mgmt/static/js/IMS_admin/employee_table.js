$(document).ready(function() {
    var table = $('#myTable').DataTable({
        searching: true, // Enable searching
        lengthMenu: [5, 10, 25, 50, 100], 
        buttons: [
            {
                extend: 'copy',
                exportOptions: {
                    columns: [1, 2, 3, 4, 5, 6] 
                }
            },
            {
                extend: 'csv',
                exportOptions: {
                    columns: [1, 2, 3, 4, 5, 6] 
                }
            },
            {
                extend: 'pdf',
                exportOptions: {
                    columns: [1, 2, 3, 4, 5, 6] 
                }
            }
        ]
    });

    $('#addProductBtn').on('click', function() {
        // Open the modal for adding products
        $('#addModal').modal('show');
    });

    $('#csvExportBtn').on('click', function() {
        table.buttons('.buttons-csv').trigger();
    });

    $('#pdfExportBtn').on('click', function() {
        table.buttons('.buttons-pdf').trigger();
    });


    $('#copyBtn').on('click', function() {
        table.buttons('.buttons-copy').trigger();
    });
});
document.getElementById("addProductBtn").onclick = function () {
        location.href = "{% url 'add_employee' %}";
    };

    document.getElementById("deleteForm{{ product.id }}").addEventListener("submit", function(event) {
        var confirmation = confirm("Are you sure you want to delete this Employee?");
        if (!confirmation) {
            event.preventDefault();
        }
    });