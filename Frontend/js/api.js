/**
 * API Module - Handles all backend API calls
 */
const API_BASE = 'http://localhost:5000/api';

const api = {
    async getStops() {
        try {
            const response = await fetch(`${API_BASE}/stops`);
            const data = await response.json();
            if (!data.success) throw new Error(data.error);
            return data.data;
        } catch (error) {
            console.error('Failed to fetch stops:', error);
            throw error;
        }
    },

    async getGrievances() {
        try {
            const response = await fetch(`${API_BASE}/grievances`);
            const data = await response.json();
            if (!data.success) throw new Error(data.error);
            return data.data;
        } catch (error) {
            console.error('Failed to fetch grievances:', error);
            throw error;
        }
    },

    async getReport() {
        try {
            const response = await fetch(`${API_BASE}/report`);
            const data = await response.json();
            return data.data;
        } catch (error) {
            console.error('Error fetching report:', error);
            return null;
        }
    },

    async getTrends() {
        try {
            const response = await fetch(`${API_BASE}/trends`);
            const data = await response.json();
            return data.data;
        } catch (error) {
            console.error('Error fetching trends:', error);
            return null;
        }
    },

    async getStopDetails(stopId) {
        try {
            const response = await fetch(`${API_BASE}/stops/${stopId}/details`);
            const data = await response.json();
            if (!data.success) throw new Error(data.error);
            return data.data;
        } catch (error) {
            console.error('Error fetching stop details:', error);
            return null;
        }
    },

    async getChecklist() {
        try {
            const response = await fetch(`${API_BASE}/checklist`);
            const data = await response.json();
            if (!data.success) throw new Error(data.error);
            return data.data;
        } catch (error) {
            console.error('Failed to fetch checklist:', error);
            throw error;
        }
    }
};
