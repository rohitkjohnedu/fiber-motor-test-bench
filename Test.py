class PlotUpdater:
    def __init__(self, plotHistoryLength):
        self.plotHistoryLength = plotHistoryLength
    
    def update_plot(self, t, y1):
        # Just print the data for demonstration
        print("Updating plot with data:")
        for i in range(len(t)):
            print(f"t={t[i]}, y1={y1[i]}")

    def process_data(self, tplot, hv_vm):
        if len(tplot) > 0:
            last_time = tplot[-1]
            use = [t > last_time - self.plotHistoryLength for t in tplot]
            self.update_plot(t=[t for i, t in enumerate(tplot) if use[i]], y1=[y for i, y in enumerate(hv_vm) if use[i]])

# Example usage
if __name__ == "__main__":
    # Initialize PlotUpdater with plotHistoryLength of 10 seconds
    plot_updater = PlotUpdater(plotHistoryLength=10)

    # Sample data for tplot and hv_vm
    tplot = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]  # Time series data
    hv_vm = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140]  # Corresponding values

    # Process the data
    plot_updater.process_data(tplot, hv_vm)
