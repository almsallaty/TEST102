
/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc_service";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class ExecutiveDashboard extends Component {
    static template = "baroon_dealership.ExecutiveDashboard";

    setup() {
        this.state = useState({
            loaded: false,
            hero: {},
            alerts: [],
            sales_trend: [],
            stock_distribution: {},
            top_models: [],
            salespeople: [],
            currency: {},
        });
        this.action = useService("action");
        this.chartRefs = { trend: useRef("trend"), dist: useRef("dist") };
        this.charts = {};
        onMounted(async () => { await this.load(); });
        onWillUnmount(() => this.destroyCharts());
    }

    async load() {
        this.state.loaded = false;
        const data = await jsonrpc("/baroon/dashboard/data", {});
        Object.assign(this.state, data, { loaded: true });
        this.renderCharts();
    }

    async refresh() { await this.load(); }

    destroyCharts() {
        if (this.charts.trend) { this.charts.trend.destroy(); this.charts.trend = null; }
        if (this.charts.dist) { this.charts.dist.destroy(); this.charts.dist = null; }
    }

    renderCharts() {
        if (!window.ApexCharts || !this.state.loaded || !this.chartRefs.trend.el || !this.chartRefs.dist.el) {
            return;
        }
        this.destroyCharts();
        this.charts.trend = new window.ApexCharts(this.chartRefs.trend.el, {
            chart: { type: "line", height: 280, toolbar: { show: false } },
            series: [{ name: "Units Sold", data: this.state.sales_trend.map((x) => x.count) }],
            xaxis: { categories: this.state.sales_trend.map((x) => `M${x.month}`) },
            colors: ["#0B1C3F"],
            stroke: { curve: "smooth", width: 3 },
            markers: { size: 4 },
        });
        this.charts.trend.render();
        this.charts.dist = new window.ApexCharts(this.chartRefs.dist.el, {
            chart: { type: "donut", height: 280 },
            series: [
                this.state.stock_distribution.available || 0,
                this.state.stock_distribution.reserved || 0,
                this.state.stock_distribution.pipeline || 0,
                this.state.stock_distribution.sold || 0,
                this.state.stock_distribution.delivered || 0,
            ],
            labels: ["Available", "Reserved", "Pipeline", "Sold", "Delivered"],
            colors: ["#16A34A", "#F59E0B", "#0EA5E9", "#0B1C3F", "#6B7280"],
            legend: { position: "bottom" },
        });
        this.charts.dist.render();
    }

    open(model, domain) {
        this.action.doAction({ type: "ir.actions.act_window", res_model: model, view_mode: "list,form,kanban", domain });
    }
    openInventory() { this.open("stock.lot", [["is_car_vehicle", "=", true], ["active", "=", true]]); }
    openAvailable() { this.open("stock.lot", [["is_car_vehicle", "=", true], ["car_status", "=", "available"]]); }
    openSold() { this.open("stock.lot", [["is_car_vehicle", "=", true], ["car_status", "in", ["sold", "delivered"]]]); }
    handleAlert(alert) {
        if (alert.action === "open_aging") this.open("stock.lot", [["is_car_vehicle", "=", true], ["days_in_stock", ">", 90]]);
        else if (alert.action === "open_missing_images") this.open("stock.lot", [["is_car_vehicle", "=", true], ["display_cover_image", "=", false]]);
    }
}

registry.category("actions").add("baroon_executive_dashboard", ExecutiveDashboard);
