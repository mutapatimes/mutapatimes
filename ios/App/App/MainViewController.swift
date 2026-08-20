import UIKit
import Capacitor

/// Adds a real native pull-to-refresh (UIRefreshControl) to the web view's
/// scroll view. The app's review notes already describe pull-to-refresh as
/// a native touch; this is what actually makes that true, rather than
/// relying on the page's own scroll bounce, which does nothing.
class MainViewController: CAPBridgeViewController {
    private let refreshControl = UIRefreshControl()

    override func viewDidLoad() {
        super.viewDidLoad()
        refreshControl.addTarget(self, action: #selector(handleRefresh), for: .valueChanged)
        webView?.scrollView.refreshControl = refreshControl
        webView?.scrollView.bounces = true
    }

    @objc private func handleRefresh() {
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
        webView?.reload()
        // The page reload itself takes over the visual state; give the
        // spinner a moment on screen rather than yanking it away instantly.
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) { [weak self] in
            self?.refreshControl.endRefreshing()
        }
    }
}
