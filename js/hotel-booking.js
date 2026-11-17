/*
 * Hotel booking widget (hotel reviews).
 *
 * The widget is a plain GET form that opens the hotel's booking engine
 * with the dates and guest count as query parameters, so it works with
 * no JavaScript at all. This script only adds the conveniences:
 *   - sensible default dates (tomorrow, two nights)
 *   - keeps checkout after checkin as the user changes dates
 * Loaded by build_static_pages.py only on pages with [data-booking-widget].
 */
(function () {
  'use strict';

  function iso(d) {
    var m = d.getMonth() + 1, day = d.getDate();
    return d.getFullYear() + '-' + (m < 10 ? '0' : '') + m + '-' + (day < 10 ? '0' : '') + day;
  }

  function addDays(d, n) {
    var x = new Date(d.getTime());
    x.setDate(x.getDate() + n);
    return x;
  }

  var widgets = document.querySelectorAll('[data-booking-widget]');
  Array.prototype.forEach.call(widgets, function (w) {
    var form = w.querySelector('form');
    if (!form) return;
    var cin = form.querySelector('[name="checkinDate"]');
    var cout = form.querySelector('[name="checkoutDate"]');
    if (!cin || !cout) return;

    var today = new Date();
    today.setHours(0, 0, 0, 0);
    var tomorrow = addDays(today, 1);

    cin.min = iso(today);
    if (!cin.value) cin.value = iso(tomorrow);
    cout.min = iso(addDays(new Date(cin.value), 1));
    if (!cout.value) cout.value = iso(addDays(new Date(cin.value), 2));

    cin.addEventListener('change', function () {
      if (!cin.value) return;
      var start = new Date(cin.value);
      var minOut = addDays(start, 1);
      cout.min = iso(minOut);
      if (!cout.value || new Date(cout.value) <= start) cout.value = iso(addDays(start, 2));
    });
  });
})();
