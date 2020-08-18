$(function() {
  /* datatables initialization */
  var gearupTable = $('#data-table').DataTable({
    'lengthMenu': [
      [100, 250, 500, 1000, 2000, -1],
      [100, 250, 500, 1000, 2000, 'All']
    ],
    drawCallback: function() {
        $('[data-toggle="popover"]').popover({
            trigger: 'hover',
            'placement': 'right'
        });
    },
    'columnDefs': [
      { targets: 'no-sort', orderable: false }
    ],
    order: [[2, "desc"]],
    dom: 'lfrBtip',
    buttons: [
      {
        extend: 'excelHtml5',
        exportOptions: {
          columns: ':visible'
        }
      }
    ]
  });
  /* override the submit event for the alert form to handle some things */
  $('form#health-check').submit(function(){
    // disable submit button after users clicks it
    $(this).children('input[type=submit]').attr('disabled', 'disabled');
  });
});
