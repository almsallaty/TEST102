/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { getDefaultConfig } from "@web/views/view";
import { useService } from "@web/core/utils/hooks";
import { useDebounced } from "@web/core/utils/timing";
import { session } from "@web/session";
import { Domain } from "@web/core/domain";
import { sprintf } from "@web/core/utils/strings";
import { rpc } from "@web/core/network/rpc";
const { Component, useSubEnv, useState, onMounted, onWillStart, useRef } = owl;
import { loadJS, loadCSS } from "@web/core/assets"


class VehicleAvailability extends Component {
  setup() {
    this.action = useService("action");
    this.orm = useService("orm");
    this.state = useState({})
    onWillStart(async () => {
      const data = await rpc('/get/contract/data')
      if(data){
        this.state.data = data.data
      }

    })
    onMounted(() => {
        if(this.state.data){
            this.renderGanttChart(this.state.data)
        }
    })
  }
  dateValidation() {
        let dateOne = document.getElementById('filter_search').value;
        let dateTwo = document.getElementById('filter_search_end').value;

        let checkInDate = new Date(dateOne);
        let checkOutDate = new Date(dateTwo);
        let filterDiv = document.getElementById('filter');

        if (checkInDate && checkOutDate) {
            // Check if the check-out date is earlier than the check-in date
            if (checkOutDate < checkInDate) {
                if(!document.getElementById('alert_message')){
                    let alertDiv = document.createElement('div');

                    // Set the attributes
                    alertDiv.setAttribute('role', 'alert');
                    alertDiv.setAttribute('id', 'alert_message');


                    // Add the necessary classes
                    alertDiv.classList.add('text-end', 'py-2', 'm-2','text-danger');

                    // Optionally, you can set inner HTML or text content
                    alertDiv.textContent = 'It is not possible for the end date to exceed the  start date.';
                    filterDiv.appendChild(alertDiv);
                }

            } else {
               if(document.getElementById('alert_message')){
                    document.getElementById('alert_message').remove()
               }
            }
        }
  }
  async filterVehicleBookings() {
    await loadJS("/vehicle_rental/static/src/js/lib/moment.min.js");
    const start_date = this.state.start_date;
    const end_date = this.state.end_date;
    if (start_date && end_date) {
      const result = await rpc("/get/vehicle/status/by/date", {
        start_date: moment(start_date).format('DD-MM-YYYY'),
        end_date: moment(end_date).format('DD-MM-YYYY'),
      });
      if (result) {
        this.state.data = result.data;
        this.renderGanttChart(this.state.data)
      }
    }

  }

  async renderGanttChart(contractdata) {
    let el = await document.getElementById('availibilityChart')
    if (el.innerHTML != '') {
        gantt.clearAll()
        el.innerHTML = ''
    }
    var tasks = {
        data: contractdata
    };

    const handleTaskClick = async (taskName) => {
            const domain = [
                ['reference_no', '=', taskName],
            ];
            const records = await this.orm.searchRead('vehicle.contract', domain, ['id']);
            let context = { 'create': false }
            return await this.action.doAction({
                type: 'ir.actions.act_window',
                name: 'contracts',
                res_model: 'vehicle.contract',
                res_id: records[0].id,
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'current',
                context: context,
            });
        };

        gantt.templates.task_class = function (start, end, task) {
            if (task.prop == "main") {
                return "hidden-task";
            }
            return "";
        };

        gantt.templates.task_text = function (start, end, task) {
            return `<div class="task-text" data-task-name="${task.text}">${task.text}</div>`;
        };

        gantt.config.min_column_width = 50;
        gantt.config.readonly = true;
        gantt.config.date_format = "%d-%m-%Y %H:%i:%s";  // match python strftime output

        gantt.config.columns = [
            { name: "text", label: "Vehicle", tree: true, width: 200 },
            {
                name: "customer_name",
                label: "Customer",
                align: "right",
                width: 150,
                template: function (task) {
                    if (task.prop === "sub" && task.customer_name) {
                        return task.customer_name;
                    }
                    return "";
                }
            },
            {
                name: "reference_no",
                label: "Contract",
                align: "center",
                width: 120,
                template: function (task) {
                    if (task.prop === "sub" && task.reference_no) {
                        return task.reference_no;
                    }
                    return "";
                }
            },
            {
                name: "start_date",
                label: "Start Date",
                align: "center",
                width: 130,
                template: function (task) {
                    if (task.prop === "sub" && task.start_date) {
                        // Format: 17-02-2026 14:30
                        let d = task.start_date;
                        let day = String(d.getDate()).padStart(2, '0');
                        let month = String(d.getMonth() + 1).padStart(2, '0');
                        let year = d.getFullYear();
                        let hours = String(d.getHours()).padStart(2, '0');
                        let mins = String(d.getMinutes()).padStart(2, '0');
                        return `${day}-${month}-${year} ${hours}:${mins}`;
                    }
                    return "";
                }
            },
            {
                name: "end_date",
                label: "End Date",
                align: "center",
                width: 130,
                template: function (task) {
                    if (task.prop === "sub" && task.end_date) {
                        let d = task.end_date;
                        let day = String(d.getDate()).padStart(2, '0');
                        let month = String(d.getMonth() + 1).padStart(2, '0');
                        let year = d.getFullYear();
                        let hours = String(d.getHours()).padStart(2, '0');
                        let mins = String(d.getMinutes()).padStart(2, '0');
                        return `${day}-${month}-${year} ${hours}:${mins}`;
                    }
                    return "";
                }
            },
            {
                name: "duration",
                label: "Duration (hrs)",
                align: "center",
                width: 100,
                template: function (task) {
                    if (task.prop === "sub" && task.duration_hours) {
                        let totalHours = Math.floor(task.duration_hours);
                        let minutes = Math.round((task.duration_hours - totalHours) * 60);
                        if (minutes > 0) {
                            return `${totalHours}h ${minutes}m`;
                        }
                        return `${totalHours}h`;
                    }
                    return "";
                }
            }
        ];

        gantt.templates.grid_folder = function (item) {
            if (item.prop === "main") {
                return "<img class='gantt_tree_icon' src='/vehicle_rental/static/src/img/vehicle.svg' alt='img'/>";
            } else {
                return "<img class='gantt_tree_icon' src='/vehicle_rental/static/src/img/contract.svg' alt='img'/>";
            }
        };

        gantt.templates.grid_file = function (item) {
            if (item.prop === "main") {
                return "<img class='gantt_tree_icon' src='/vehicle_rental/static/src/img/vehicle.svg' alt='img'/>";
            } else {
                return "<img class='gantt_tree_icon' src='/vehicle_rental/static/src/img/contract.svg' alt='img'/>";
            }
        };

        gantt.init(el);
        gantt.parse(tasks);

        el.addEventListener('click', function (event) {
            if (event.target.classList.contains('task-text')) {
                const taskId = event.target.getAttribute('data-task-name');
                handleTaskClick(taskId);
            }
        });
    }


}
VehicleAvailability.template = "vehicle_rental.availability_vehicle";
registry.category("actions").add("vehicle_availability", VehicleAvailability);
