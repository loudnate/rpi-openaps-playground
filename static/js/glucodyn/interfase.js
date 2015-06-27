/**
 * @param {object} event The event descriptor
 * @param {number} time The simulation time, in minutes
 * @return {number} The glucose effect, in mg/dL
 */
function eventEffectAtTime(event, time) {
    if(event.etype=="carb") {
        return deltaBGC(time - event.time, userdata.sensf, userdata.cratio, event.grams, event.ctype)
    } else if(event.etype=="bolus") {
        return deltaBGI(time - event.time, event.units, userdata.sensf, userdata.idur)
    } else {
        return deltatempBGI(time, event.dbdt, userdata.sensf, userdata.idur, event.t1, event.t2);
    }
}

// Function to load the Graph everytime any setting is changed
function reloadGraphData() {

    var simt = userdata.simlength*60;
    var dt=simt/n;

    for (i=0;i<n;i++) {
        simbg[i]=userdata.bginitial;
        simbgc[i]=0.0;
        simbgi[i]=0.0;
    }

    for (j = 0; j < uevent.length; j++) {

        if ( uevent[j] && uevent.etype != "" ) {

            var t0effect = eventEffectAtTime(uevent[j], 0);

            for (i=0; i<n;i++) {
                var netEffectAtTime = eventEffectAtTime(uevent[j], i * dt) - t0effect;

                if(uevent[j].etype=="carb") {
                    simbgc[i] = simbgc[i] + netEffectAtTime;
                } else if(uevent[j].etype=="bolus") {
                    simbgi[i] = simbgi[i] + netEffectAtTime;
                } else {
                    simbgi[i] = simbgi[i] + netEffectAtTime;
                }
            }

        }

    }

    var hAxisTitle = 'Time (min)';

    if (userdata.pump_time_string) {
        hAxisTitle += ' from ' + userdata.pump_time_string;
    }

    var predata = new google.visualization.DataTable();
    predata.addColumn('number', hAxisTitle); // Implicit domain label col.
    predata.addColumn('number', 'Resulting Blood Sugar mg/dL'); // Implicit series 1 data col.

    if ( userdata.stats == 1 ) {

        // Show stats table
        document.getElementById("statistics_container").classList.remove("hidden");

        if ( userdata.inputeffect == 1 ) {

            predata.addColumn('number', 'Carb effect on Blood Sugar mg/dL'); // Implicit series 1 data col.
            predata.addColumn('number', 'Insulin effect on Blood Sugar mg/dL'); // Implicit series 1 data col.

        }

        predata.addColumn('number', 'Average mg/dL');
        predata.addColumn('number', 'Min mg/dL');
        predata.addColumn('number', 'Max mg/dL');

        for (i=0;i<n;i++) {
            simbg[i]=userdata.bginitial+simbgc[i]+simbgi[i];
        }

        var stats = GlucodynStats(simbg);

        for (i=0;i<n;i++) {
            if ( userdata.inputeffect == 1 ){
                predata.addRow([(dt*i)+1,simbg[i],userdata.bginitial+simbgc[i],userdata.bginitial+simbgi[i],stats[0], stats[2], stats[3]]);
            }else{
                predata.addRow([(dt*i)+1,simbg[i],stats[0], stats[2], stats[3]]);
            }
        }

        if ( userdata.inputeffect == 1 ) {

            var options = {
                height: 500,
                backgroundColor: 'transparent',
                title: '',
                curveType: 'function',
                legend: { position: 'bottom' },
                hAxis: {
                    title: hAxisTitle,
                    baselineColor: 'none'
                },
                vAxis: {
                    title: 'BG mg/dL',
                    baselineColor: 'none'
                },
                legend: {
                    textStyle: {
                        fontSize: 14
                    }
                },
                series: {
                    0: { color: '#666666' },
                    1: { color: '#1abc9c', lineDashStyle: [4,4] },
                    2: { color: '#e74c3c', lineDashStyle: [4,4] },
                    3: { color: '#999999', lineDashStyle: [12,4], lineWidth:1 },
                    4: { color: '#999999', lineDashStyle: [12,4], lineWidth:1 },
                    5: { color: '#999999', lineDashStyle: [12,4], lineWidth:1 }
                },
                chartArea: {'width': '90%', 'height': '80%'},
                legend: {'position': 'top'}
            };

        } else {

            var options = {
                height: 500,
                backgroundColor: 'transparent',
                title: '',
                curveType: 'function',
                legend: { position: 'bottom' },
                hAxis: {
                    title: hAxisTitle,
                    baselineColor: 'none'
                },
                vAxis: {
                    title: 'BG mg/dL',
                    baselineColor: 'none'
                },
                legend: {
                    textStyle: {
                        fontSize: 14
                    }
                },
                series: {
                    0: { color: '#666666' },
                    1: { color: '#999999', lineDashStyle: [12,4], lineWidth:1 },
                    2: { color: '#999999', lineDashStyle: [12,4], lineWidth:1 },
                    3: { color: '#999999', lineDashStyle: [12,4], lineWidth:1 }
                },
                chartArea: {'width': '90%', 'height': '80%'},
                legend: {'position': 'top'}
            };

        }

    } else {

        // Hide stats table
        document.getElementById("statistics_container").classList.add("hidden");
        document.getElementById("stats_avg").innerText = "N/A";
        document.getElementById("stats_min").innerText = "N/A";
        document.getElementById("stats_max").innerText = "N/A";
        document.getElementById("stats_std").innerText = "N/A";

        if ( userdata.inputeffect == 1 ) {

            predata.addColumn('number', 'Carb effect on Blood Sugar mg/dL'); // Implicit series 1 data col.
            predata.addColumn('number', 'Insulin effect on Blood Sugar mg/dL'); // Implicit series 1 data col.

        }

        for (i=0;i<n;i++) {
            simbg[i]=userdata.bginitial+simbgc[i]+simbgi[i];

            if ( userdata.inputeffect == 1 ) {
                predata.addRow([(dt*i)+1,simbg[i],userdata.bginitial+simbgc[i],userdata.bginitial+simbgi[i]]);
            }else{
                predata.addRow([(dt*i)+1,simbg[i]]);
            }

        }

        if ( userdata.inputeffect == 1 ) {

            var options = {
                height: 500,
                backgroundColor: 'transparent',
                title: '',
                curveType: 'function',
                legend: { position: 'bottom' },
                hAxis: {
                    title: hAxisTitle,
                    baselineColor: 'none'
                },
                vAxis: {
                    title: 'BG mg/dL',
                    baselineColor: 'none'
                },
                legend: {
                    textStyle: {
                        fontSize: 14
                    }
                },
                series: {
                    0: { color: '#666666' },
                    1: { color: '#1abc9c', lineDashStyle: [4,4] },
                    2: { color: '#e74c3c', lineDashStyle: [4,4] },
                },
                chartArea: {'width': '90%', 'height': '80%'}
            };

        } else {

            var options = {
                height: 500,
                backgroundColor: 'transparent',
                title: '',
                curveType: 'function',
                legend: { position: 'bottom' },
                hAxis: {
                    title: hAxisTitle,
                    baselineColor: 'none'
                },
                vAxis: {
                    title: 'BG mg/dL',
                    baselineColor: 'none'
                },
                legend: {
                    textStyle: {
                        fontSize: 14
                    }
                },
                series: {
                    0: { color: '#666666' },
                },
                chartArea: {'width': '90%', 'height': '80%'}
            };

        }

    }

    var chart = new google.visualization.LineChart(document.getElementById('curve_chart'));

    chart.draw(predata, options);

}

// Event History
function addEventHistory() {

    var event = uevent[uevent.length - 1];
    var event_index = uevent.length - 1;
    var event_id = event_index
    var description = ""

    if(event.etype == "carb") {
        description = "<span id='amount_label_" + event_id +"'>" + event.grams + "</span> gr of carbs (" + event.ctype + " min absorption time)";
        description_b = "Taken @ min <span id='time_label_" + event_id +"'>"+ event.time +"</span>"
    } else if(event.etype=="bolus") {
        description = "<span id='amount_label_" + event_id +"'>" + event.units + "</span> U insulin input";
        description_b = "Taken @ min <span id='time_label_" + event_id +"'>"+ event.time +"</span>"
    } else if (event.etype=="tempbasal") {
        description = "" + event.dbdt + " U/min temp basal input";
        description_b = "From min "+ event.t1 +" to min "+ event.t2 +""
    }

    var row = document.createElement("div");
    row.id = "uevent_" + event_id;
    row.className = "row";
    row.innerHTML = "<div class='col-xs-6'>" + description + "</div><div class='col-xs-6'>" + description_b + "</div>";
    document.getElementById("input_history").appendChild(row);

    document.getElementById("input_history_container").classList.remove("hidden");

}

// Document Ready
document.addEventListener('readystatechange', function() {
    reloadGraphData();

    window.addEventListener('resize', function() {
        reloadGraphData()
    })
});
