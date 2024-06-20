$(document).ready(function() {
    var table = $('#myTable').DataTable({
        searching: true, // Enable searching
        lengthMenu: [5, 10, 25, 50, 100], // Show entries dropdown options
        buttons: [
            'copy', 'csv', 'pdf', 'print'
        ]
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