'''
@author: lthero
@personal web: lthero.cn
'''
from wallhaven_downloader.core import download_from_search, download_wallpapers


class No_UI(object):
    def __init__(self, path, sorting, toprange, purity='110', categories='110', start_page=1, num=1):
        self.file = path
        self.sorting = sorting
        self.topRange = toprange
        self.purity = purity or '110'
        self.categories = categories or '110'
        self.num = num
        self.start_page = start_page

    def down_load(self, url, num, file_path):
        results = download_wallpapers(url, int(num), file_path)
        self.print_results(results)
        return results

    def condition_down(self):
        if self.file == '':
            print('先选择路径')
            return []

        results = download_from_search(
            output_dir=self.file,
            sorting=self.sorting,
            top_range=self.topRange,
            purity=self.purity,
            categories=self.categories,
            start_page=int(self.start_page),
            page_count=int(self.num),
        )
        self.print_results(results)
        return results

    @staticmethod
    def print_results(results):
        downloaded = sum(1 for item in results if not item.skipped and item.error is None)
        skipped = sum(1 for item in results if item.skipped)
        failed = [item for item in results if item.error is not None]
        print(f'下载完成：成功 {downloaded} 张，跳过 {skipped} 张，失败 {len(failed)} 张')
        for item in failed:
            print(f'失败 {item.wallpaper_id}: {item.error}')


if __name__ == '__main__':
    pa = input('输入路径')
    start_p = int(input('起始页数'))
    pages = int(input('输入要下载页数'))
    arr_stort = ['date_added', 'toplist', 'favorites', 'views', 'hot', 'random']
    sorte = int(input('输入排序方式：0、date_added 1、toplist 2、favorites 3、views 4、hot 5、random\n'))
    arr_time = ['1w', '1M', '3M', '6M', '1y', '1d']
    times = int(input('输入时间：0、上周 1、近一个月的 2、近三个月的 3、近六个月的 4、一年 5、最新的\n'))
    pur = input('输入SFW  Sketchy NSFW  默认110\n') or '110'
    cat = input('输入普通  动漫   真人   默认110\n') or '110'
    cin = No_UI(pa, arr_stort[sorte], arr_time[times], pur, cat, start_p, pages)
    cin.condition_down()
